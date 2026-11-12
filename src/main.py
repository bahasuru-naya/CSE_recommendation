"""Main entry point and CLI commands for the CSE Stock Recommendation System."""

from __future__ import annotations

import argparse
import logging
import sys

from src.alerts.telegram import TelegramAlerter
from src.core.calendar import TradingCalendarBuilder
from src.core.price_daily import DailyPriceBuilder
from src.core.reconciliation import DataReconciler
from src.core.security_master import SecurityMasterBuilder
from src.db import SessionLocal
from src.engine.decision import DecisionEngine
from src.features.builder import FeatureBuilder
from src.ingestion.orchestrator import IngestionOrchestrator
from src.models.lgbm_model import CSELightGBMModel
from src.models.registry import ModelRegistry
from src.scheduler.jobs import PipelineScheduler
from src.utils.time_utils import trading_date

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cse_system")


def cmd_daily(target_date=None):
    """Run full daily sequence: Ingestion -> Promotion -> Features -> Decisions -> Alerts."""
    t_date = target_date or trading_date()
    logger.info("==================================================")
    logger.info("Starting Daily CSE Recommendation Run for %s", t_date)
    logger.info("==================================================")

    session = SessionLocal()
    try:
        # 1. Ingestion
        orch = IngestionOrchestrator(session)
        orch.run_daily_ingestion(t_date)

        # 2. Promote to Core
        price_builder = DailyPriceBuilder(session)
        price_builder.process_staging_trade_summary(t_date)
        price_builder.process_indices(t_date)

        # 3. Features
        feat_builder = FeatureBuilder(session)
        feat_builder.build_all_features(t_date)

        # 4. Decisions
        engine = DecisionEngine(session)
        recommendations = engine.run(t_date)

        # 5. Telegram Alerts
        alerter = TelegramAlerter()
        for rec in recommendations[:3]:  # Top 3 signals
            alerter.send_recommendation(rec)

        logger.info("Daily pipeline completed successfully.")
    finally:
        session.close()


def cmd_backfill(period: int = 4):
    """Backfill historical chart data and compute features."""
    logger.info("Starting historical data backfill...")
    session = SessionLocal()
    try:
        # 1. Calendar
        cal = TradingCalendarBuilder(session)
        cal.populate(2020, 2030)

        # 2. Ingest trade summary & indices to discover all active stock symbols & IDs
        orch = IngestionOrchestrator(session)
        orch.trade_summary.sync()
        orch.market_data.sync_indices_and_summary()

        # 3. Promote staging to dim_security & fact_index_daily
        price_builder = DailyPriceBuilder(session)
        price_builder.process_staging_trade_summary()
        price_builder.process_indices()

        # 4. Backfill historical chart data
        orch.backfill_history(period=period)
        price_builder.process_staging_chart_data()

        # 5. Build historical features (all dates × all securities)
        feat_builder = FeatureBuilder(session)
        feat_builder.build_all_features_historical()
        logger.info("Backfill and historical feature generation completed.")
    finally:
        session.close()


def cmd_historical_features():
    """Compute and save historical features for every security × trading date."""
    logger.info("Starting historical feature computation for all securities...")
    session = SessionLocal()
    try:
        feat_builder = FeatureBuilder(session)
        total = feat_builder.build_all_features_historical()
        logger.info("Historical feature build complete: %d rows saved.", total)
    finally:
        session.close()


def cmd_retrain():
    """Train and register a LightGBM model version."""
    from src.api.routes.models import _train_model_job
    logger.info("Training and registering LightGBM model...")
    _train_model_job()
    logger.info("Model training completed.")


def cmd_reconcile():
    """Run data quality and reconciliation audit."""
    session = SessionLocal()
    try:
        recon = DataReconciler(session)
        report = recon.reconcile_daily()
        fresh = recon.check_freshness()
        print("\n--- DATA RECONCILIATION REPORT ---")
        for k, v in report.items():
            print(f"  {k}: {v}")
        print("\n--- FRESHNESS AUDIT ---")
        for k, v in fresh.get("tables", {}).items():
            print(f"  {k}: {v}")
        print(f"  is_stale: {fresh.get('is_stale')}\n")
    finally:
        session.close()


def cmd_serve(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """Run FastAPI uvicorn server."""
    import uvicorn
    logger.info("Starting API server on %s:%d...", host, port)
    uvicorn.run("src.api.main:app", host=host, port=port, reload=reload)


def cmd_schedule():
    """Start the APScheduler background daemon."""
    scheduler = PipelineScheduler()
    scheduler.start()
    logger.info("Scheduler running in foreground. Press Ctrl+C to terminate.")
    try:
        import time
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


def main():
    parser = argparse.ArgumentParser(description="CSE Stock Recommendation Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # daily
    subparsers.add_parser("daily", help="Run full daily end-of-day pipeline")

    # backfill
    p_backfill = subparsers.add_parser("backfill", help="Backfill historical chart series")
    p_backfill.add_argument("--period", type=int, default=4, help="Chart history period code (1-5)")

    # historical-features
    subparsers.add_parser("historical-features", help="Compute historical features for all securities × all dates")

    # schedule
    subparsers.add_parser("schedule", help="Start background scheduler daemon")

    # smoke-test
    subparsers.add_parser("smoke-test", help="Test CSE API connectivity and schema")

    # retrain
    subparsers.add_parser("retrain", help="Train and register a new LightGBM model version")

    # reconcile
    subparsers.add_parser("reconcile", help="Run data lake reconciliation and freshness audit")

    # serve
    p_serve = subparsers.add_parser("serve", help="Run FastAPI web server")
    p_serve.add_argument("--host", default="127.0.0.1", help="Bind host")
    p_serve.add_argument("--port", type=int, default=8000, help="Bind port")
    p_serve.add_argument("--reload", action="store_true", help="Enable live code reload")

    args = parser.parse_args()

    if args.command == "daily":
        cmd_daily()
    elif args.command == "backfill":
        cmd_backfill(period=args.period)
    elif args.command == "historical-features":
        cmd_historical_features()
    elif args.command == "schedule":
        cmd_schedule()
    elif args.command == "smoke-test":
        from scripts.smoke_test import run_smoke_test
        run_smoke_test()
    elif args.command == "retrain":
        cmd_retrain()
    elif args.command == "reconcile":
        cmd_reconcile()
    elif args.command == "serve":
        cmd_serve(host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
