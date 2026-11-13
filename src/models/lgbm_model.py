"""LightGBM model for predicting 10-day alpha over ASPI benchmark net of costs."""

from __future__ import annotations

import io
import logging
import pickle
from collections.abc import Callable
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd
import shap
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger(__name__)


class CSELightGBMModel:
    """Predicts probability of beating ASPI by >round-trip cost over 10 trading days.

    Improvements over baseline
    --------------------------
    1. Features are *normalised* before training: raw price-level columns (SMA, EMA,
       Bollinger, MACD, ATR) are expressed as ratios to the current close price so the
       model is not sensitive to absolute price magnitude of different CSE stocks.
    2. Class imbalance (~3.35:1 negative) is handled via ``scale_pos_weight`` computed
       from the actual training label distribution rather than a fixed constant.
    3. Regularisation parameters are tightened (shallower trees, higher min-leaf
       samples, L1/L2 penalties, reduced feature/bagging fractions, lower LR) to
       reduce overfitting on the small CSE dataset (~13 k rows).
    4. Walk-forward cross-validation is available via ``cross_validate()`` to give a
       stable AUC estimate across time folds without data leakage.
    """

    # Raw price-level columns that must be normalised before training/inference.
    # These are divided by the contemporaneous close price to remove magnitude bias.
    _PRICE_LEVEL_COLS: list[str] = [
        "sma_5", "sma_10", "sma_20", "sma_50", "sma_100",
        "ema_12", "ema_26",
        "bollinger_upper", "bollinger_lower",
        "macd", "macd_signal", "macd_histogram",
        "atr_14",
    ]

    # Final feature list used by the model (normalised versions replace raw ones).
    FEATURE_COLUMNS: list[str] = [
        # Short-horizon returns (dimensionless; excludes forward-looking 10d/20d)
        "return_1d", "return_5d",
        # Normalised moving-average ratios  (price / close – 1)
        "sma_5_ratio", "sma_10_ratio", "sma_20_ratio", "sma_50_ratio", "sma_100_ratio",
        "ema_12_ratio", "ema_26_ratio",
        # Normalised MACD ratios
        "macd_ratio", "macd_signal_ratio", "macd_histogram_ratio",
        # Normalised Bollinger bands
        "bollinger_upper_ratio", "bollinger_lower_ratio", "bollinger_width",
        # Oscillators (already 0-100 or dimensionless)
        "rsi_14", "stochastic_k", "stochastic_d",
        # Volatility (already annualised pct)
        "volatility_20d", "aspi_volatility_20d",
        # Normalised ATR
        "atr_14_ratio",
        # Volume features
        "volume_ratio", "avg_daily_volume_20d", "avg_daily_turnover_20d",
        # Relative strength vs index (dimensionless)
        "rs_vs_aspi_5d", "rs_vs_aspi_20d",
        # Distance from 52-week extremes (already pct)
        "dist_from_52w_high", "dist_from_52w_low",
    ]

    # Anti-overfit parameters tuned for CSE's dataset size (~13k rows, 300+ stocks)
    DEFAULT_PARAMS: dict[str, Any] = {
        "objective": "binary",
        "metric": "auc",
        "boosting_type": "gbdt",
        # Shallow trees → lower variance
        "num_leaves": 20,
        "max_depth": 5,
        "min_child_samples": 40,   # each leaf needs ≥40 samples
        "min_child_weight": 1e-3,
        # Regularisation
        "reg_alpha": 0.1,          # L1 sparsity
        "reg_lambda": 1.0,         # L2 smoothing
        # Stochastic sub-sampling (reduces variance)
        "feature_fraction": 0.65,
        "bagging_fraction": 0.75,
        "bagging_freq": 3,
        # Low LR with high round limit; early-stopping decides when to quit
        "learning_rate": 0.03,
        "n_estimators": 600,
        "verbose": -1,
    }

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        self.params = {**self.DEFAULT_PARAMS, **(params or {})}
        self.model: lgb.Booster | None = None
        self.explainer: shap.TreeExplainer | None = None
        self.calibrator: LogisticRegression | None = None
        # close-price series stored at training time for inference normalisation
        self._close_col_present: bool = False

    # ------------------------------------------------------------------
    # Feature normalisation
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise_features(X: pd.DataFrame) -> pd.DataFrame:
        """Return copy of X with price-level columns normalised to close price.

        For each col in _PRICE_LEVEL_COLS the raw value is replaced by
        ``(raw / close) - 1`` (a percentage deviation from current price).
        MACD and ATR can be negative or zero so they are simply divided by
        close (not shifted by 1) to give a price-relative scale.
        The original raw columns are dropped after normalisation.
        A ``close`` or ``price`` column is used for normalisation and then
        dropped from the output so it never enters the model as a feature.
        """
        X = X.copy()

        close = None
        for col in ("price", "close"):
            if col in X.columns:
                close = X[col].replace(0, np.nan)
                break

        if close is None:
            # No close available – skip normalisation (inference without price col)
            return X

        for raw_col in CSELightGBMModel._PRICE_LEVEL_COLS:
            if raw_col not in X.columns:
                continue
            ratio_col = f"{raw_col}_ratio"
            if raw_col in ("macd", "macd_signal", "macd_histogram", "atr_14"):
                # Can be negative: divide by close to get price-relative scale
                X[ratio_col] = X[raw_col] / close
            else:
                # Moving averages: express as % distance from current price
                X[ratio_col] = (X[raw_col] / close) - 1.0
            X = X.drop(columns=[raw_col], errors="ignore")

        # Drop the close / price column; it must not be a feature
        X = X.drop(columns=["close", "price"], errors="ignore")
        return X

    # ------------------------------------------------------------------
    # Target construction
    # ------------------------------------------------------------------

    @staticmethod
    def create_target(
        stock_prices: pd.Series,
        aspi_prices: pd.Series,
        horizon_days: int = 10,
        round_trip_cost: float = 0.0268,  # CSE commission + SEC/CSE levies buy+sell
    ) -> pd.Series:
        """Create forward-looking target for training only (never leak to features).

        Target = 1 if (Stock_t+H / Stock_t - 1) > (ASPI_t+H / ASPI_t - 1) + round_trip_cost.
        Inputs must be aligned on the same trading-session dates.
        """
        stock_fwd_ret = stock_prices.shift(-horizon_days) / stock_prices - 1.0
        aspi_fwd_ret = aspi_prices.shift(-horizon_days) / aspi_prices - 1.0
        excess_return = stock_fwd_ret - aspi_fwd_ret
        valid = (
            stock_prices.notna()
            & aspi_prices.notna()
            & np.isfinite(stock_prices)
            & np.isfinite(aspi_prices)
            & stock_prices.gt(0)
            & aspi_prices.gt(0)
            & stock_fwd_ret.notna()
            & aspi_fwd_ret.notna()
            & np.isfinite(stock_fwd_ret)
            & np.isfinite(aspi_fwd_ret)
        )
        target = (excess_return > round_trip_cost).where(valid).astype(float)
        return target

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame | None = None,
        y_val: pd.Series | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Train LightGBM classifier with early stopping and class-imbalance handling.

        Steps
        -----
        1. Drop warm-up rows with NaN indicator values (RSI, volatility) so
           misleading fill values from new listings (e.g. RSI=50, vol=0) are
           excluded from training.  Production inference is unaffected: rows
           with insufficient history will receive a neutral probability and the
           caller should map them to WATCH.
           # NOTE: src/features/technical.py still uses fillna(50.0) for RSI and
           # fillna(0.0) for volatility.  Those should be changed to fillna(np.nan)
           # so this warm-up mask actually fires.  Until that change is in place,
           # the mask below acts as a safeguard for any NaN rows already present.
        2. Normalise price-level features (SMA, EMA, MACD, Bollinger, ATR → ratios).
        3. Compute ``scale_pos_weight`` from actual label distribution.
        4. Train with early stopping on the validation set (not the training set).
        5. Initialise SHAP explainer for inference.
        """
        # Step 1 – drop warm-up rows that have NaN in key indicators to avoid
        # misleading filled values (e.g. RSI filled with 50, volatility with 0)
        # for stocks with insufficient price history from corrupting training.
        # The warm-up period is RSI(14) + buffer = ~20 rows minimum.
        WARMUP_COLS = ["rsi_14", "volatility_20d"]
        warmup_mask = pd.Series(True, index=X_train.index)
        for col in WARMUP_COLS:
            if col in X_train.columns:
                warmup_mask &= X_train[col].notna()
        n_before = len(X_train)
        X_train = X_train.loc[warmup_mask]
        y_train = y_train.loc[warmup_mask]
        n_dropped = n_before - len(X_train)
        if n_dropped > 0:
            logger.info(
                "Warm-up filter: dropped %d rows with NaN RSI/volatility (insufficient history).",
                n_dropped,
            )
        # Step 1 – normalise
        X_train_norm = self._normalise_features(X_train)
        feature_cols = [c for c in self.FEATURE_COLUMNS if c in X_train_norm.columns]
        if not feature_cols:
            raise ValueError("Training data does not contain any supported model features.")
        X_train_clean = (
            X_train_norm[feature_cols]
            .apply(pd.to_numeric, errors="coerce")
            .fillna(0.0)
        )

        # Step 2 – class-imbalance weight
        if X_train.empty:
            raise ValueError("No training rows remain after filtering insufficient feature history.")
        if not X_train.index.equals(y_train.index):
            raise ValueError("X_train and y_train must have matching indexes.")

        pos = int(y_train.sum())
        neg = int(len(y_train) - pos)
        if pos == 0 or neg == 0:
            raise ValueError("Training labels must contain both positive and negative samples.")
        scale_pos_weight = neg / pos
        logger.info(
            "Training: pos=%d neg=%d scale_pos_weight=%.2f", pos, neg, scale_pos_weight
        )
        train_params = {**self.params, "scale_pos_weight": scale_pos_weight}

        # Step 3 – build LightGBM datasets
        train_data = lgb.Dataset(X_train_clean, label=y_train)

        valid_sets = []
        callbacks = []
        if X_val is not None and y_val is not None and len(X_val) > 0:
            if not X_val.index.equals(y_val.index):
                raise ValueError("X_val and y_val must have matching indexes.")
            val_mask = pd.Series(True, index=X_val.index)
            for col in WARMUP_COLS:
                if col in X_val.columns:
                    val_mask &= X_val[col].notna()
            X_val = X_val.loc[val_mask]
            y_val = y_val.loc[val_mask]
        if X_val is not None and y_val is not None and len(X_val) > 0 and y_val.nunique() > 1:
            X_val_norm = self._normalise_features(X_val)
            X_val_clean = (
                X_val_norm.reindex(columns=feature_cols)
                .apply(pd.to_numeric, errors="coerce")
                .fillna(0.0)
            )
            val_data = lgb.Dataset(X_val_clean, label=y_val, reference=train_data)
            valid_sets = [val_data]
            logger.info("Using separate validation set (%d rows) for early stopping.", len(X_val_clean))
        else:
            logger.warning(
                "No usable two-class validation set provided; training for the configured number of rounds."
            )

        num_rounds = int(train_params.get("n_estimators", 600))
        if valid_sets:
            callbacks = [lgb.early_stopping(stopping_rounds=40, verbose=True)]
        if progress_callback is not None:
            def report_progress(env: Any) -> None:
                iteration = env.iteration + 1
                if iteration == 1 or iteration % 10 == 0 or iteration == env.end_iteration:
                    progress_callback(iteration, env.end_iteration)

            report_progress.order = 20
            callbacks.append(report_progress)

        self.model = lgb.train(
            train_params,
            train_data,
            num_boost_round=num_rounds,
            valid_sets=valid_sets or None,
            callbacks=callbacks,
        )
        self.calibrator = None

        # Step 4 – SHAP explainer
        try:
            self.explainer = shap.TreeExplainer(self.model)
        except Exception as exc:
            logger.warning("SHAP TreeExplainer initialisation skipped: %s", exc)

        importance = dict(
            zip(
                feature_cols,
                self.model.feature_importance(importance_type="gain").tolist(),
                strict=True,
            )
        )
        logger.info(
            "Training complete: best_iteration=%d, features=%d",
            self.model.best_iteration or num_rounds,
            len(feature_cols),
        )
        return {
            "status": "trained",
            "best_iteration": self.model.best_iteration,
            "feature_importance": importance,
            "scale_pos_weight": round(scale_pos_weight, 3),
            "train_pos": pos,
            "train_neg": neg,
            "train_samples": len(y_train),
        }

    # ------------------------------------------------------------------
    # Walk-forward cross-validation
    # ------------------------------------------------------------------

    def cross_validate(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_splits: int = 5,
        dates: pd.Series | None = None,
    ) -> dict[str, Any]:
        """Walk-forward (time-series) cross-validation.

        Splits are made by whole trading dates. Each outer validation window is
        preceded by a 10-session purge; a separate earlier window is used for
        early stopping so reported fold metrics are out-of-sample.

        Note: this trains a *temporary* model per fold and does **not** update
        ``self.model``.  Call ``train()`` separately on the full dataset after
        cross-validating.
        """
        from sklearn.metrics import accuracy_score, roc_auc_score

        if n_splits < 2:
            raise ValueError("n_splits must be at least 2.")
        if dates is None:
            if "trading_date" in X.columns:
                dates = X["trading_date"]
            elif isinstance(X.index, pd.DatetimeIndex):
                dates = pd.Series(X.index, index=X.index)
            else:
                raise ValueError("Trading dates must be supplied for leakage-safe cross-validation.")
        if not dates.index.equals(X.index) or not X.index.equals(y.index):
            raise ValueError("X, y, and dates must have matching indexes.")

        horizon = 10
        session_dates = pd.DatetimeIndex(pd.to_datetime(dates)).normalize().unique().sort_values()
        if len(session_dates) <= n_splits * (horizon + 1):
            raise ValueError("Insufficient trading dates for the requested purged folds.")
        date_positions = {day: position for position, day in enumerate(session_dates)}
        row_positions = pd.to_datetime(dates).dt.normalize().map(date_positions)
        fold_size = len(session_dates) // (n_splits + 1)
        aucs, accs = [], []

        for fold in range(1, n_splits + 1):
            outer_start = fold * fold_size
            outer_end = min((fold + 1) * fold_size, len(session_dates))
            outer_train_end = outer_start - horizon
            inner_start = int(outer_train_end * 0.8)
            inner_train_end = inner_start - horizon
            if inner_train_end <= 0 or outer_end <= outer_start:
                continue

            train_mask = row_positions.lt(inner_train_end)
            early_mask = row_positions.ge(inner_start) & row_positions.lt(outer_train_end)
            fold_mask = row_positions.ge(outer_start) & row_positions.lt(outer_end)
            history_mask = pd.Series(True, index=X.index)
            for col in ("rsi_14", "volatility_20d"):
                if col in X.columns:
                    history_mask &= X[col].notna()
            train_mask &= history_mask
            early_mask &= history_mask
            fold_mask &= history_mask
            Xtr, ytr = X.loc[train_mask], y.loc[train_mask]
            Xes, yes = X.loc[early_mask], y.loc[early_mask]
            Xvl, yvl = X.loc[fold_mask], y.loc[fold_mask]
            if (
                len(ytr) < 50
                or len(yes) < 10
                or len(yvl) < 10
                or ytr.nunique() < 2
                or yes.nunique() < 2
                or yvl.nunique() < 2
            ):
                continue

            tmp = CSELightGBMModel(params=self.params)
            tmp.train(Xtr, ytr, Xes, yes)
            tmp.fit_calibrator(Xes, yes)
            probs = tmp.predict_proba(Xvl)
            auc = roc_auc_score(yvl, probs)
            acc = accuracy_score(yvl, (probs >= 0.50).astype(int))
            aucs.append(auc)
            accs.append(acc)
            logger.info("CV fold %d/%d: AUC=%.4f Acc=%.4f", fold, n_splits, auc, acc)

        return {
            "n_folds": len(aucs),
            "mean_auc": round(float(np.mean(aucs)), 4) if aucs else None,
            "std_auc": round(float(np.std(aucs)), 4) if aucs else None,
            "mean_acc": round(float(np.mean(accs)), 4) if accs else None,
            "fold_aucs": [round(a, 4) for a in aucs],
        }

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def _predict_raw(self, X: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            raise ValueError("Model has not been trained or loaded yet.")
        X_norm = self._normalise_features(X)
        if hasattr(self.model, "feature_name") and callable(self.model.feature_name):
            feature_cols = self.model.feature_name()
        else:
            feature_cols = [c for c in self.FEATURE_COLUMNS if c in X_norm.columns]
        X_eval = (
            X_norm.reindex(columns=feature_cols)
            .apply(pd.to_numeric, errors="coerce")
            .fillna(0.0)
        )
        return np.asarray(self.model.predict(X_eval), dtype=float)

    def fit_calibrator(self, X_cal: pd.DataFrame, y_cal: pd.Series) -> None:
        """Calibrate class-weighted model scores on a chronological validation window."""
        if not X_cal.index.equals(y_cal.index):
            raise ValueError("X_cal and y_cal must have matching indexes.")
        if y_cal.nunique() < 2:
            raise ValueError("Probability calibration requires both validation classes.")
        raw_scores = self._predict_raw(X_cal)
        self.calibrator = LogisticRegression(C=1.0, solver="lbfgs")
        self.calibrator.fit(raw_scores.reshape(-1, 1), y_cal.astype(int))

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict probabilities of beating the benchmark.

        Input ``X`` may contain raw price-level columns; they are normalised
        to ratios before inference, matching the training pipeline.
        """
        raw_scores = self._predict_raw(X)
        if self.calibrator is None:
            return raw_scores
        return self.calibrator.predict_proba(raw_scores.reshape(-1, 1))[:, 1]

    # ------------------------------------------------------------------
    # Explanation
    # ------------------------------------------------------------------

    def explain(self, X_row: pd.DataFrame, top_n: int = 5) -> list[dict[str, Any]]:
        """Explain single-observation prediction using SHAP."""
        X_norm = self._normalise_features(X_row)

        if hasattr(self.model, "feature_name") and callable(self.model.feature_name):
            feature_cols = self.model.feature_name()
        else:
            feature_cols = [c for c in self.FEATURE_COLUMNS if c in X_norm.columns]

        X_eval = (
            X_norm.reindex(columns=feature_cols)
            .apply(pd.to_numeric, errors="coerce")
            .fillna(0.0)
        )

        if self.explainer is not None:
            try:
                shap_vals = self.explainer.shap_values(X_eval)
                if isinstance(shap_vals, list):
                    vals = shap_vals[1][0] if len(shap_vals) > 1 else shap_vals[0][0]
                else:
                    vals = shap_vals[0]

                pairs = sorted(zip(feature_cols, vals, strict=True), key=lambda x: abs(x[1]), reverse=True)
                return [{"feature": f, "impact": round(float(v), 4)} for f, v in pairs[:top_n]]
            except Exception as exc:
                logger.debug("SHAP explanation failed: %s", exc)

        # Fallback to feature importance
        if self.model:
            imp = self.model.feature_importance(importance_type="gain")
            pairs = sorted(zip(feature_cols, imp, strict=True), key=lambda x: x[1], reverse=True)
            return [{"feature": f, "impact": round(float(v), 2)} for f, v in pairs[:top_n]]
        return []

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_bytes(self) -> bytes:
        """Serialise model for database storage."""
        buf = io.BytesIO()
        pickle.dump(
            {"model": self.model, "params": self.params, "calibrator": self.calibrator},
            buf,
        )
        return buf.getvalue()

    @classmethod
    def from_bytes(cls, data: bytes) -> "CSELightGBMModel":
        """Restore model from database binary payload."""
        loaded = pickle.loads(data)
        instance = cls(params=loaded.get("params"))
        instance.model = loaded.get("model")
        instance.calibrator = loaded.get("calibrator")
        try:
            if instance.model:
                instance.explainer = shap.TreeExplainer(instance.model)
        except Exception:
            pass
        return instance
