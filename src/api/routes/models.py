"""Machine Learning model management, backtests, and registry API."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import numpy as np
import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.db import SessionLocal, get_db
from src.engine.decision import DecisionEngine
from src.engine.position_sizing import PositionSizer
from src.models.backtester import CostAwareBacktester
from src.models.lgbm_model import CSELightGBMModel
from src.models.regime_filter import RegimeFilter
from src.models.registry import ModelRegistry
from src.utils.time_utils import trading_date

logger = logging.getLogger(__name__)
router = APIRouter()

_LABEL_HORIZON = 10
_ROUND_TRIP_COST = 0.0268
_retrain_jobs: dict[str, dict[str, Any]] = {}
_retrain_jobs_lock = threading.Lock()


def _update_retrain_job(job_id: str, **updates: Any) -> None:
    with _retrain_jobs_lock:
        job = _retrain_jobs.get(job_id)
        if job is not None:
            job.update(updates)


def _get_retrain_job(job_id: str) -> dict[str, Any] | None:
    with _retrain_jobs_lock:
        job = _retrain_jobs.get(job_id)
        return job.copy() if job is not None else None


def _fill_no_trade_metrics(
    metrics: dict[str, Any],
    benchmark_return_pct: float | None,
) -> dict[str, Any]:
    """Use the backtester's cash-return convention when no positions were opened."""
    result = dict(metrics)
    if "total_trades" not in result:
        return result

    try:
        if int(result["total_trades"] or 0) != 0:
            return result
    except (TypeError, ValueError):
        return result

    for metric in ("sharpe_ratio", "win_rate", "total_return"):
        if result.get(metric) is None:
            result[metric] = 0.0
    if result.get("excess_return") is None and benchmark_return_pct is not None:
        result["excess_return"] = round(-benchmark_return_pct, 2)
    return result


def _get_benchmark_return_pct(
    db: Session,
    start_date: str | None,
    end_date: str | None,
) -> float | None:
    if not start_date or not end_date:
        return None

    rows = db.execute(
        text("""
            SELECT trading_date, close
            FROM core.fact_index_daily
            WHERE index_name = 'ASPI'
              AND trading_date >= CAST(:start_date AS DATE) - INTERVAL '10 days'
              AND trading_date <= CAST(:end_date AS DATE)
            ORDER BY trading_date
        """),
        {"start_date": start_date, "end_date": end_date},
    ).fetchall()
    if len(rows) < 2:
        return None

    closes = pd.DataFrame(rows, columns=["trading_date", "close"])
    closes["trading_date"] = pd.to_datetime(closes["trading_date"])
    closes["close"] = pd.to_numeric(closes["close"], errors="coerce")
    closes = closes.loc[
        closes["trading_date"].notna()
        & closes["close"].gt(0)
        & np.isfinite(closes["close"])
    ].sort_values("trading_date")
    returns = closes["close"].pct_change(fill_method=None)
    evaluation_start = pd.Timestamp(start_date)
    evaluation_returns = returns.loc[closes["trading_date"] >= evaluation_start].dropna()
    if evaluation_returns.empty or not np.isfinite(evaluation_returns).all():
        return None
    return float((np.prod(1.0 + evaluation_returns.to_numpy()) - 1.0) * 100.0)


def _build_forward_alpha_targets(
    prices: pd.DataFrame,
    aspi: pd.DataFrame,
    horizon: int = _LABEL_HORIZON,
    round_trip_cost: float = _ROUND_TRIP_COST,
) -> pd.DataFrame:
    """Build targets on exact exchange-session dates, not per-security row counts."""
    if horizon < 1:
        raise ValueError("Target horizon must be at least one trading session.")
    if prices.empty or aspi.empty:
        raise ValueError("Stock and ASPI price history are required to build targets.")

    price_rows = prices[["security_id", "trading_date", "price"]].copy()
    market_rows = aspi[["trading_date", "close"]].copy()
    price_rows["trading_date"] = pd.to_datetime(price_rows["trading_date"]).dt.normalize()
    market_rows["trading_date"] = pd.to_datetime(market_rows["trading_date"]).dt.normalize()
    price_rows["price"] = pd.to_numeric(price_rows["price"], errors="coerce")
    market_rows["close"] = pd.to_numeric(market_rows["close"], errors="coerce")
    market_rows = market_rows.dropna(subset=["trading_date", "close"]).drop_duplicates(
        "trading_date", keep="last"
    )
    market_dates = pd.DatetimeIndex(market_rows["trading_date"].sort_values().unique())
    if len(market_dates) <= horizon:
        raise ValueError(f"Need more than {horizon} ASPI trading sessions to create labels.")

    future_dates = dict(zip(market_dates[:-horizon], market_dates[horizon:], strict=True))
    aspi_prices = market_rows.set_index("trading_date")["close"]
    future_prices = price_rows.rename(
        columns={"trading_date": "future_date", "price": "future_price"}
    )[["security_id", "future_date", "future_price"]]
    labeled = price_rows.assign(future_date=lambda frame: frame["trading_date"].map(future_dates))
    labeled = labeled.merge(
        future_prices,
        on=["security_id", "future_date"],
        how="left",
        validate="many_to_one",
    )
    labeled["aspi_price"] = labeled["trading_date"].map(aspi_prices)
    labeled["future_aspi_price"] = labeled["future_date"].map(aspi_prices)
    labeled["forward_excess"] = (
        labeled["future_price"] / labeled["price"] - 1.0
    ) - (labeled["future_aspi_price"] / labeled["aspi_price"] - 1.0)
    valid = (
        labeled["price"].gt(0)
        & labeled["future_price"].gt(0)
        & labeled["aspi_price"].gt(0)
        & labeled["future_aspi_price"].gt(0)
        & labeled["forward_excess"].notna()
        & np.isfinite(labeled["price"])
        & np.isfinite(labeled["future_price"])
        & np.isfinite(labeled["aspi_price"])
        & np.isfinite(labeled["future_aspi_price"])
        & np.isfinite(labeled["forward_excess"])
    )
    labeled = labeled.loc[valid].copy()
    labeled["target"] = (labeled["forward_excess"] > round_trip_cost).astype(int)
    return labeled[
        ["security_id", "trading_date", "future_date", "price", "forward_excess", "target"]
    ]


def _chronological_date_masks(
    dates: pd.Series,
    market_dates: pd.Series | pd.DatetimeIndex,
    horizon: int = _LABEL_HORIZON,
) -> dict[str, pd.Series]:
    """Split by whole market sessions and purge label-overlap windows."""
    session_dates = pd.DatetimeIndex(pd.to_datetime(market_dates)).normalize().unique().sort_values()
    if len(session_dates) <= 3 * horizon + 20:
        raise ValueError("Insufficient trading-date history for purged train/validation/test splits.")

    validation_start = int(len(session_dates) * 0.70)
    test_start = int(len(session_dates) * 0.85)
    train_end = validation_start - horizon
    validation_end = test_start - horizon
    if train_end <= 0 or validation_end <= validation_start:
        raise ValueError("Insufficient trading dates after applying the label purge windows.")

    date_positions = {day: position for position, day in enumerate(session_dates)}
    row_positions = pd.to_datetime(dates).dt.normalize().map(date_positions)
    return {
        "train": row_positions.lt(train_end),
        "validation": row_positions.ge(validation_start) & row_positions.lt(validation_end),
        "test": row_positions.ge(test_start),
    }


def _execute_full_retrain(
    session: Session,
    update_predictions: bool = True,
    run_backtest: bool = True,
    progress_callback: Callable[[str, int, str], None] | None = None,
) -> dict[str, Any]:
    """Train using stored features, evaluate an untouched holdout, and gate promotion."""
    logger.info("Starting model retrain pipeline...")

    def report(stage: str, progress: int, message: str) -> None:
        logger.info("Model retrain %d%% [%s]: %s", progress, stage, message)
        if progress_callback is not None:
            progress_callback(stage, progress, message)

    report("loading_data", 5, "Loading existing feature and price history from the database.")
    feature_query = text("""
        SELECT f.*, p.close AS current_price,
               COALESCE(NULLIF(p.adj_close, 0), p.close) AS price,
               s.symbol
        FROM features.feature_daily f
        JOIN core.fact_price_daily p
          ON p.security_id = f.security_id AND p.trading_date = f.trading_date
        JOIN core.dim_security s ON s.security_id = f.security_id
        WHERE s.is_active = TRUE
        ORDER BY f.trading_date ASC, f.security_id ASC
    """)
    features = pd.read_sql(feature_query, session.bind)
    if features.empty:
        raise ValueError(
            "No stored feature history is available. Run the historical feature build once, then retry training."
        )

    prices_query = text("""
        SELECT security_id, trading_date, COALESCE(NULLIF(adj_close, 0), close) AS price
        FROM core.fact_price_daily
        ORDER BY trading_date ASC, security_id ASC
    """)
    prices = pd.read_sql(prices_query, session.bind)
    report("building_labels", 20, f"Loaded {len(features):,} stored feature rows; aligning stock and ASPI dates.")
    aspi_query = text("""
        SELECT trading_date, close
        FROM core.fact_index_daily
        WHERE index_name = 'ASPI'
        ORDER BY trading_date ASC
    """)
    aspi = pd.read_sql(aspi_query, session.bind)
    targets = _build_forward_alpha_targets(prices, aspi)

    features["trading_date"] = pd.to_datetime(features["trading_date"]).dt.normalize()
    targets["trading_date"] = pd.to_datetime(targets["trading_date"]).dt.normalize()
    df = features.merge(
        targets.drop(columns=["price"]),
        on=["security_id", "trading_date"],
        how="inner",
        validate="many_to_one",
    ).sort_values(["trading_date", "security_id"]).reset_index(drop=True)
    if df.empty:
        raise ValueError("No feature rows have complete 10-session stock and ASPI labels.")
    report("splitting_data", 28, f"Created {len(df):,} labeled rows from the existing database data.")

    aspi["trading_date"] = pd.to_datetime(aspi["trading_date"]).dt.normalize()
    market_dates = pd.DatetimeIndex(aspi["trading_date"].dropna().unique()).sort_values()
    masks = _chronological_date_masks(df["trading_date"], market_dates)

    required_history = ("rsi_14", "volatility_20d")
    missing_features = [name for name in required_history if name not in df.columns]
    if missing_features:
        raise ValueError(f"Required warm-up indicators are missing: {', '.join(missing_features)}.")
    has_history = df[list(required_history)].notna().all(axis=1)
    masks = {name: mask & has_history for name, mask in masks.items()}

    drop_cols = {
        "security_id", "trading_date", "as_of_date", "future_date",
        "forward_excess", "target", "symbol",
    }
    X = df.drop(columns=list(drop_cols), errors="ignore")
    y = df["target"].astype(int)
    X_train, y_train = X.loc[masks["train"]], y.loc[masks["train"]]
    X_val, y_val = X.loc[masks["validation"]], y.loc[masks["validation"]]
    X_test, y_test = X.loc[masks["test"]], y.loc[masks["test"]]
    df_test = df.loc[masks["test"]].copy()
    if X_train.empty or X_val.empty or X_test.empty:
        raise ValueError("Not enough feature rows in all three purged chronological data splits.")
    if y_val.nunique() < 2:
        raise ValueError("Early-stopping and probability calibration data must contain both classes.")

    logger.info(
        "Purged date split: %d train / %d early-stop validation / %d final holdout rows",
        len(X_train),
        len(X_val),
        len(X_test),
    )

    def report_training_progress(iteration: int, total_iterations: int) -> None:
        training_progress = min(66, 36 + int(30 * iteration / max(total_iterations, 1)))
        report(
            "training",
            training_progress,
            f"Training LightGBM: iteration {iteration:,} of {total_iterations:,}.",
        )

    report(
        "training",
        35,
        f"Training on {len(X_train):,} rows; early-stopping validation has {len(X_val):,} rows.",
    )
    model = CSELightGBMModel()
    train_res = model.train(X_train, y_train, X_val, y_val, progress_callback=report_training_progress)
    report("evaluation", 68, "Evaluating calibrated probabilities on the untouched holdout.")
    model.fit_calibrator(X_val, y_val)
    best_iter = int(train_res.get("best_iteration", 0) or model.params.get("n_estimators", 0))

    test_probs = model.predict_proba(X_test)
    test_binary = (test_probs >= 0.50).astype(int)
    val_auc = float(roc_auc_score(y_test, test_probs)) if y_test.nunique() > 1 else None
    val_acc = float(accuracy_score(y_test, test_binary))
    val_prec = float(precision_score(y_test, test_binary, zero_division=0))
    val_rec = float(recall_score(y_test, test_binary, zero_division=0))
    buy_binary = (test_probs >= 0.65).astype(int)
    buy_precision = float(precision_score(y_test, buy_binary, zero_division=0))
    buy_recall = float(recall_score(y_test, buy_binary, zero_division=0))
    baseline_acc = float(max(y_test.mean(), 1.0 - y_test.mean()))
    brier_score = float(np.mean((test_probs - y_test.to_numpy()) ** 2))

    raw_importance = train_res.get("feature_importance", {})
    total_gain = sum(raw_importance.values()) or 1.0
    sorted_features = sorted(raw_importance.items(), key=lambda item: item[1], reverse=True)
    top_features = [
        {"feature": feature, "importance": round(float(gain / total_gain * 100), 2)}
        for feature, gain in sorted_features[:10]
    ]

    backtest_metrics_dict: dict[str, Any] = {
        "sharpe_ratio": None,
        "win_rate": None,
        "max_drawdown": None,
        "total_return": None,
        "excess_return": None,
        "annualized_return": None,
        "final_capital": None,
        "total_trades": 0,
    }
    test_start_date = market_dates[int(len(market_dates) * 0.85)]
    test_end_date = df_test["trading_date"].max()
    if run_backtest:
        report("backtest", 74, "Running holdout-only backtest against ASPI.")
        price_query = text("""
            SELECT p.trading_date, s.symbol, p.security_id,
                   p.open, p.high, p.low, p.close
            FROM core.fact_price_daily p
            JOIN core.dim_security s ON s.security_id = p.security_id
            ORDER BY p.trading_date ASC, p.security_id ASC
        """)
        prices_df = pd.read_sql(price_query, session.bind)
        prices_df["trading_date"] = pd.to_datetime(prices_df["trading_date"]).dt.normalize()
        test_end_date = prices_df["trading_date"].max()
        df_test["confidence"] = test_probs
        df_test["signal"] = "HOLD"
        df_test["position_size_pct"] = 0.0
        df_test["stop_pct"] = 0.08
        df_test["target_pct"] = 0.15

        regime_filter = RegimeFilter()
        position_sizer = PositionSizer(total_portfolio_value=1_000_000.0)
        aspi = aspi.dropna(subset=["trading_date", "close"]).sort_values("trading_date")
        aspi_dates = aspi["trading_date"].tolist()
        aspi_prices = aspi["close"].astype(float).tolist()
        regimes: dict[pd.Timestamp, dict[str, Any]] = {}
        for day in df_test["trading_date"].drop_duplicates():
            end = int(np.searchsorted(aspi_dates, day, side="right"))
            if end:
                regimes[day] = regime_filter.classify_from_prices(aspi_prices[:end])

        for idx, row in df_test.iterrows():
            probability = float(row["confidence"])
            day = row["trading_date"]
            regime = regimes.get(day, {"allow_buy": False, "position_scale": 0.0})
            turnover = row.get("avg_daily_turnover_20d")
            volume = row.get("avg_daily_volume_20d")
            avg_turnover = float(turnover) if pd.notna(turnover) else 0.0
            avg_volume = float(volume) if pd.notna(volume) else 0.0
            liquid = avg_turnover >= 200_000.0 and avg_volume >= 500
            if not liquid:
                continue
            if probability <= 0.35:
                df_test.at[idx, "signal"] = "SELL"
                continue
            if probability < 0.65 or not regime["allow_buy"]:
                continue

            current_price = float(row["current_price"])
            model_price = float(row["price"])
            raw_atr = row.get("atr_14")
            adjustment_factor = model_price / current_price if current_price > 0 else 1.0
            atr = (
                float(raw_atr) / adjustment_factor
                if pd.notna(raw_atr) and float(raw_atr) > 0 and adjustment_factor > 0
                else current_price * 0.03
            )
            stop_loss = max(current_price - 2.0 * atr, 0.05)
            sizing = position_sizer.size(
                entry_price=current_price,
                stop_loss=stop_loss,
                avg_daily_volume=avg_volume,
                confidence=probability,
                position_scale=float(regime["position_scale"]),
            )
            df_test.at[idx, "signal"] = "BUY"
            df_test.at[idx, "position_size_pct"] = sizing["position_size_pct"]
            df_test.at[idx, "stop_pct"] = min(max((2.0 * atr) / current_price, 0.001), 0.95)
            df_test.at[idx, "target_pct"] = min(max((3.0 * atr) / current_price, 0.001), 5.0)

        bt = CostAwareBacktester(initial_capital=1_000_000.0)
        metrics, _ = bt.run(
            df_test[
                [
                    "trading_date", "security_id", "symbol", "signal", "confidence",
                    "position_size_pct", "stop_pct", "target_pct",
                ]
            ],
            prices_df,
            benchmark_returns=aspi.set_index("trading_date")["close"].pct_change().dropna(),
            eval_start_date=test_start_date,
        )
        backtest_metrics_dict = {
            "sharpe_ratio": round(float(metrics.sharpe_ratio), 2),
            "win_rate": round(float(metrics.win_rate), 1),
            "max_drawdown": round(float(metrics.max_drawdown_pct), 2),
            "total_return": round(float(metrics.total_return_pct), 2),
            "excess_return": round(float(metrics.excess_return_pct), 2),
            "annualized_return": round(float(metrics.annualized_return_pct), 2),
            "final_capital": round(float(metrics.final_capital), 2),
            "total_trades": metrics.total_trades,
        }
        report("backtest", 88, f"Backtest finished with {metrics.total_trades:,} closed trades.")

    metrics_payload = {
        "train_samples": train_res["train_samples"],
        "val_samples": len(X_test),
        "best_iteration": best_iter,
        "val_auc": round(val_auc, 4) if val_auc is not None else None,
        "accuracy": round(val_acc * 100, 2),
        "precision": round(val_prec * 100, 2),
        "recall": round(val_rec * 100, 2),
        "precision_at_buy_threshold": round(buy_precision * 100, 2),
        "recall_at_buy_threshold": round(buy_recall * 100, 2),
        "baseline_accuracy": round(baseline_acc * 100, 2),
        "brier_score": round(brier_score, 5),
        "probability_calibration": "platt",
        "evaluation_start": test_start_date.date().isoformat(),
        "evaluation_end": test_end_date.date().isoformat(),
        "forward_horizon_sessions": _LABEL_HORIZON,
        "scale_pos_weight": round(train_res.get("scale_pos_weight", 1.0), 3),
        "train_pos_samples": train_res.get("train_pos", 0),
        "train_neg_samples": train_res.get("train_neg", 0),
        "sharpe_ratio": backtest_metrics_dict["sharpe_ratio"],
        "win_rate": backtest_metrics_dict["win_rate"],
        "max_drawdown": backtest_metrics_dict["max_drawdown"],
        "total_return": backtest_metrics_dict["total_return"],
        "excess_return": backtest_metrics_dict["excess_return"],
        "total_trades": backtest_metrics_dict["total_trades"],
        "top_features": top_features,
    }

    registry = ModelRegistry(session)
    report("registration", 91, "Saving the evaluated model and metrics.")
    model_id = registry.register(
        model_name="CSE-LightGBM-Alpha",
        model_type="lightgbm",
        model_instance=model,
        hyperparameters=model.params,
        metrics=metrics_payload,
        feature_columns=model.FEATURE_COLUMNS,
    )

    registry.promote(model_id)
    report(
        "registration",
        95,
        "Newest trained model promoted as active.",
    )

    session.execute(
        text("""
            INSERT INTO ml.backtests (
                model_id, strategy_name, test_start, test_end,
                initial_capital, final_capital, total_return,
                annualized_return, sharpe_ratio, max_drawdown,
                win_rate, total_trades, excess_return, created_at
            ) VALUES (
                :model_id, 'Purged Holdout Alpha Net',
                :test_start, :test_end, 1000000.0, :final_capital, :total_return,
                :annualized_return, :sharpe, :max_drawdown,
                :win_rate, :trades, :excess_return, NOW()
            )
        """),
        {
            "model_id": model_id,
            "test_start": test_start_date.date(),
            "test_end": test_end_date.date(),
            "final_capital": backtest_metrics_dict["final_capital"],
            "total_return": backtest_metrics_dict["total_return"],
            "annualized_return": backtest_metrics_dict["annualized_return"],
            "sharpe": backtest_metrics_dict["sharpe_ratio"],
            "max_drawdown": backtest_metrics_dict["max_drawdown"],
            "win_rate": backtest_metrics_dict["win_rate"],
            "trades": backtest_metrics_dict["total_trades"],
            "excess_return": backtest_metrics_dict["excess_return"],
        },
    )
    session.commit()

    recs_count = 0
    signals_summary: dict[str, int] = {}
    prediction_update: dict[str, Any] = {
        "status": "skipped" if not update_predictions else "pending",
        "date": None,
        "count": 0,
        "error": None,
    }
    if update_predictions:
        report("predictions", 97, "Updating recommendations using the newly activated model.")
        try:
            prediction_date = session.execute(
                text("""
                    SELECT MAX(f.trading_date)
                    FROM features.feature_daily f
                    JOIN core.fact_price_daily p
                      ON p.security_id = f.security_id AND p.trading_date = f.trading_date
                    JOIN core.dim_security s ON s.security_id = f.security_id
                    WHERE s.is_active = TRUE AND f.trading_date <= :latest_allowed_date
                """),
                {"latest_allowed_date": trading_date()},
            ).scalar()
            if prediction_date is None:
                raise ValueError("No matching stored features and prices are available for prediction.")

            engine = DecisionEngine(session)
            recs = engine.run(prediction_date)
            recs_count = len(recs)
            for recommendation in recs:
                signal = recommendation.get("signal", "OTHER")
                signals_summary[signal] = signals_summary.get(signal, 0) + 1
            if not recs:
                raise RuntimeError(
                    f"No recommendations were generated for {prediction_date}; check data freshness and feature rows."
                )
            prediction_update = {
                "status": "updated",
                "date": prediction_date.isoformat(),
                "count": recs_count,
                "error": None,
            }
        except Exception as exc:
            logger.error("Failed to generate fresh predictions after retrain: %s", exc, exc_info=True)
            session.rollback()
            prediction_update = {
                "status": "failed",
                "date": None,
                "count": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }

    deleted_models = registry.prune_old_versions("CSE-LightGBM-Alpha", keep=5)

    new_ver = session.execute(
        text("SELECT version FROM ml.model_registry WHERE model_id = :id"),
        {"id": model_id},
    ).scalar()
    prediction_message = (
        f"Predictions updated for {prediction_update['date']} ({recs_count} recommendations)."
        if prediction_update["status"] == "updated"
        else f"Predictions were not updated: {prediction_update['error']}"
        if prediction_update["status"] == "failed"
        else "Prediction update was not requested."
    )
    logger.info("Model retrain completed: version %s, %d recs updated.", new_ver, recs_count)
    report(
        "completed",
        100,
        f"Model v{new_ver} is active; removed {deleted_models} older versions. {prediction_message}",
    )
    return {
        "status": "success",
        "message": (
            f"LightGBM model v{new_ver} trained and activated. "
            f"Removed {deleted_models} older versions. {prediction_message}"
        ),
        "model_id": model_id,
        "version": new_ver,
        "metrics": metrics_payload,
        "recommendations_updated": recs_count,
        "prediction_update": prediction_update,
        "models_deleted": deleted_models,
        "signals_summary": signals_summary,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/")
def list_models(db: Session = Depends(get_db)):
    """List all registered models and active status."""
    query = text("""
        SELECT model_id, model_name, model_type, version, metrics, is_active, promoted_at, created_at
        FROM ml.model_registry
        ORDER BY version DESC
    """)
    rows = db.execute(query).fetchall()
    models = []
    for row in rows:
        model_metrics = row[4] or {}
        if row[5] and model_metrics.get("total_trades") is not None:
            try:
                has_no_trades = int(model_metrics["total_trades"] or 0) == 0
            except (TypeError, ValueError):
                has_no_trades = False
            if has_no_trades:
                benchmark_return = _get_benchmark_return_pct(
                    db,
                    model_metrics.get("evaluation_start"),
                    model_metrics.get("evaluation_end"),
                )
                model_metrics = _fill_no_trade_metrics(model_metrics, benchmark_return)
        models.append({
            "model_id": row[0],
            "model_name": row[1],
            "model_type": row[2],
            "version": row[3],
            "metrics": model_metrics,
            "is_active": row[5],
            "promoted_at": row[6].isoformat() if row[6] else None,
            "created_at": row[7].isoformat() if row[7] else None,
        })
    return models


@router.post("/retrain")
def trigger_retrain(
    background_tasks: BackgroundTasks,
    async_mode: bool = Query(default=False, description="Run in background or synchronous"),
    update_predictions: bool = Query(default=True, description="Generate fresh recommendations after retrain"),
    db: Session = Depends(get_db),
):
    """Retrain from stored database data and optionally run the work asynchronously."""
    if async_mode:
        job_id = uuid4().hex
        with _retrain_jobs_lock:
            if any(job["status"] in {"queued", "running"} for job in _retrain_jobs.values()):
                raise HTTPException(status_code=409, detail="A model training job is already running.")
            _retrain_jobs[job_id] = {
                "job_id": job_id,
                "status": "queued",
                "stage": "queued",
                "progress": 0,
                "message": "Training job queued.",
                "error": None,
                "result": None,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

        def bg_run(training_job_id: str) -> None:
            _update_retrain_job(
                training_job_id,
                status="running",
                stage="starting",
                progress=1,
                message="Training started.",
                updated_at=datetime.now(timezone.utc).isoformat(),
            )
            session = SessionLocal()
            try:
                result = _execute_full_retrain(
                    session,
                    update_predictions=update_predictions,
                    progress_callback=lambda stage, progress, message: _update_retrain_job(
                        training_job_id,
                        stage=stage,
                        progress=progress,
                        message=message,
                        updated_at=datetime.now(timezone.utc).isoformat(),
                    ),
                )
                _update_retrain_job(
                    training_job_id,
                    status="completed",
                    stage="completed",
                    progress=100,
                    message=result["message"],
                    result=result,
                    updated_at=datetime.now(timezone.utc).isoformat(),
                )
            except Exception as exc:
                logger.exception("Model retraining job %s failed.", training_job_id)
                _update_retrain_job(
                    training_job_id,
                    status="failed",
                    stage="failed",
                    message="Model training failed.",
                    error={"type": type(exc).__name__, "message": str(exc)},
                    updated_at=datetime.now(timezone.utc).isoformat(),
                )
            finally:
                session.close()

        background_tasks.add_task(bg_run, job_id)
        return {
            "status": "accepted",
            "job_id": job_id,
            "message": "Model training queued using existing database data; no internet fetch is performed.",
        }

    # Synchronous execution
    try:
        result = _execute_full_retrain(db, update_predictions=update_predictions)
        return result
    except Exception as e:
        logger.error("Retrain failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retrain/status/{job_id}")
def get_retrain_status(job_id: str):
    """Return progress or error details for an asynchronous retraining job."""
    job = _get_retrain_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Training job was not found or has expired.")
    return job


@router.post("/predict")
def generate_predictions(db: Session = Depends(get_db)):
    """Generate fresh predictions and update app.recommendations using the active model."""
    try:
        engine = DecisionEngine(db)
        t_date = trading_date()
        recs = engine.run(t_date)
        breakdown: dict[str, int] = {}
        for r in recs:
            s = r.get("signal", "OTHER")
            breakdown[s] = breakdown.get(s, 0) + 1

        return {
            "status": "success",
            "message": f"Successfully generated {len(recs)} predictions for {t_date}.",
            "trading_date": str(t_date),
            "recommendations_count": len(recs),
            "signals_breakdown": breakdown,
        }
    except Exception as e:
        logger.error("Prediction generation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
def get_active_model_details(db: Session = Depends(get_db)):
    """Retrieve details and metrics of the currently active model."""
    query = text("""
        SELECT model_id, model_name, model_type, version, hyperparameters,
               feature_columns, metrics, is_active, promoted_at, created_at
        FROM ml.model_registry
        WHERE is_active = TRUE
        ORDER BY promoted_at DESC
        LIMIT 1
    """)
    row = db.execute(query).mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No active model found")
    return dict(row)


@router.get("/performance/summary")
def get_performance_summary(db: Session = Depends(get_db)):
    """Summary of active model performance, walk-forward backtest, and feature importance."""
    # Active model
    active_q = text("""
        SELECT model_id, model_name, version, metrics, created_at, promoted_at
        FROM ml.model_registry
        WHERE is_active = TRUE
        ORDER BY promoted_at DESC LIMIT 1
    """)
    active = db.execute(active_q).mappings().fetchone()

    # Latest backtest
    backtest_q = text("""
        SELECT backtest_id, strategy_name, total_return, sharpe_ratio,
               max_drawdown, win_rate, total_trades, excess_return, created_at
        FROM ml.backtests
        ORDER BY created_at DESC LIMIT 1
    """)
    bt = db.execute(backtest_q).mappings().fetchone()

    # Recommendation counts
    rec_q = text("""
        SELECT signal, COUNT(*)
        FROM app.recommendations
        WHERE created_at >= NOW() - INTERVAL '24 hours'
        GROUP BY signal
    """)
    rec_rows = db.execute(rec_q).fetchall()
    recs_breakdown = {r[0]: r[1] for r in rec_rows}

    return {
        "active_model": dict(active) if active else None,
        "latest_backtest": dict(bt) if bt else None,
        "signals_breakdown": recs_breakdown,
    }


@router.get("/list")
def list_models_alias(db: Session = Depends(get_db)):
    """Alias for GET /models/."""
    return list_models(db)


@router.get("/{model_id}")
def get_model_details(model_id: int, db: Session = Depends(get_db)):
    """Get hyperparameters and feature importance for a model."""
    query = text("""
        SELECT model_id, model_name, model_type, version, hyperparameters,
               feature_columns, metrics, is_active, created_at
        FROM ml.model_registry
        WHERE model_id = :id
    """)
    row = db.execute(query, {"id": model_id}).mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Model not found")
    return dict(row)


@router.get("/{model_id}/backtests")
def get_model_backtests(model_id: int, db: Session = Depends(get_db)):
    """Retrieve backtest runs for model."""
    query = text("""
        SELECT backtest_id, strategy_name, test_start, test_end, total_return,
               sharpe_ratio, max_drawdown, win_rate, total_trades, excess_return
        FROM ml.backtests
        WHERE model_id = :id
        ORDER BY created_at DESC
    """)
    rows = db.execute(query, {"id": model_id}).fetchall()
    return [
        {
            "backtest_id": r[0],
            "strategy_name": r[1],
            "test_start": str(r[2]),
            "test_end": str(r[3]),
            "total_return": float(r[4]) if r[4] else None,
            "sharpe_ratio": float(r[5]) if r[5] else None,
            "max_drawdown": float(r[6]) if r[6] else None,
            "win_rate": float(r[7]) if r[7] else None,
            "total_trades": r[8],
            "excess_return": float(r[9]) if r[9] else None,
        }
        for r in rows
    ]


@router.post("/{model_id}/promote")
def promote_model(model_id: int, db: Session = Depends(get_db)):
    """Promote model version to ACTIVE."""
    registry = ModelRegistry(db)
    registry.promote(model_id)
    return {"status": "promoted", "model_id": model_id}
