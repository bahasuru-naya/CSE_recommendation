import numpy as np
import pandas as pd
import pytest
from fastapi import HTTPException

from src.api.routes.models import (
    _build_forward_alpha_targets,
    _chronological_date_masks,
    _fill_no_trade_metrics,
    _get_benchmark_return_pct,
    _retrain_jobs,
    _retrain_jobs_lock,
    get_retrain_status,
)
from src.models.registry import ModelRegistry


def test_forward_alpha_target_uses_exact_market_sessions_and_benchmark():
    sessions = pd.bdate_range("2025-01-01", periods=15)
    stock_rows = [
        {"security_id": 1, "trading_date": day, "price": 100.0 if i < 10 else 105.0}
        for i, day in enumerate(sessions)
    ]
    stock_rows.extend(
        {"security_id": 2, "trading_date": day, "price": 100.0}
        for i, day in enumerate(sessions)
        if i != 10
    )
    prices = pd.DataFrame(stock_rows)
    aspi = pd.DataFrame({"trading_date": sessions, "close": 1000.0})

    targets = _build_forward_alpha_targets(prices, aspi, horizon=10, round_trip_cost=0.0268)

    first_stock = targets.loc[
        (targets["security_id"] == 1) & (targets["trading_date"] == sessions[0])
    ].iloc[0]
    assert first_stock["target"] == 1
    assert np.isclose(first_stock["forward_excess"], 0.05)
    assert not (
        (targets["security_id"] == 2) & (targets["trading_date"] == sessions[0])
    ).any()


def test_chronological_split_purges_whole_market_sessions():
    sessions = pd.bdate_range("2025-01-01", periods=100)
    row_dates = pd.Series(sessions)

    masks = _chronological_date_masks(row_dates, sessions, horizon=10)
    positions = {day: idx for idx, day in enumerate(sessions)}
    split_positions = {
        name: [positions[day] for day in row_dates.loc[mask]]
        for name, mask in masks.items()
    }

    assert max(split_positions["train"]) < 60
    assert min(split_positions["validation"]) >= 70
    assert max(split_positions["validation"]) < 75
    assert min(split_positions["test"]) >= 85
    assert not (masks["train"] & masks["validation"]).any()
    assert not (masks["validation"] & masks["test"]).any()


def test_no_trade_metrics_use_cash_backtest_results_instead_of_missing_values():
    metrics = _fill_no_trade_metrics(
        {
            "total_trades": 0,
            "sharpe_ratio": None,
            "win_rate": None,
            "total_return": None,
            "excess_return": None,
        },
        benchmark_return_pct=4.93,
    )

    assert metrics["sharpe_ratio"] == 0.0
    assert metrics["win_rate"] == 0.0
    assert metrics["total_return"] == 0.0
    assert metrics["excess_return"] == -4.93


def test_no_trade_benchmark_return_compounds_daily_aspi_returns():
    class Result:
        def fetchall(self):
            return [
                (pd.Timestamp("2025-01-01"), 100.0),
                (pd.Timestamp("2025-01-02"), 110.0),
                (pd.Timestamp("2025-01-03"), 121.0),
            ]

    class SessionStub:
        def execute(self, *_args, **_kwargs):
            return Result()

    benchmark_return = _get_benchmark_return_pct(
        SessionStub(),
        "2025-01-02",
        "2025-01-03",
    )

    assert np.isclose(benchmark_return, 21.0)


def test_retrain_status_exposes_progress_and_reports_unknown_job():
    job_id = "test-job"
    job = {"job_id": job_id, "status": "running", "stage": "training", "progress": 42}
    with _retrain_jobs_lock:
        _retrain_jobs[job_id] = job
    try:
        assert get_retrain_status(job_id) == job
        with pytest.raises(HTTPException) as exc_info:
            get_retrain_status("missing-job")
        assert exc_info.value.status_code == 404
    finally:
        with _retrain_jobs_lock:
            _retrain_jobs.pop(job_id, None)


def test_registry_pruning_deletes_old_model_dependencies_before_versions():
    class Result:
        def fetchall(self):
            return [(10,), (11,)]

    class SessionStub:
        def __init__(self):
            self.statements = []
            self.committed = False

        def execute(self, statement, params=None):
            self.statements.append(str(statement))
            return Result()

        def commit(self):
            self.committed = True

    session = SessionStub()
    deleted = ModelRegistry(session).prune_old_versions("CSE-LightGBM-Alpha", keep=5)

    assert deleted == 2
    assert session.committed
    assert any("OFFSET :keep" in statement for statement in session.statements)
    for table in ("ml.training_runs", "ml.predictions", "ml.backtests", "ml.drift_metrics"):
        assert any(f"DELETE FROM {table}" in statement for statement in session.statements)
    assert sum("DELETE FROM ml.model_registry" in statement for statement in session.statements) == 2
