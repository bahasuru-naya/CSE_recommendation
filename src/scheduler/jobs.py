"""APScheduler-based pipeline scheduler with startup catch-up and execution tracking."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import json
import logging
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import text

from src.db import SessionLocal
from src.ingestion.orchestrator import IngestionOrchestrator
from src.core.price_daily import DailyPriceBuilder
from src.core.corporate_actions import CorporateActionProcessor
from src.core.reconciliation import DataReconciler
from src.utils.time_utils import COLOMBO_TZ, is_market_hours, trading_date

logger = logging.getLogger(__name__)


class PipelineScheduler:
    """Orchestrates recurring jobs and tracks execution history in app.job_runs."""

    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=COLOMBO_TZ)

    def _record_run(self, job_id: str, func: Callable, *args, **kwargs):
        """Wrapper to track job run start, completion, and errors in app.job_runs."""
        session = SessionLocal()
        start_time = datetime.utcnow()
        run_record_id = None

        try:
            insert_q = text("""
                INSERT INTO app.job_runs (job_id, status, started_at)
                VALUES (:job_id, 'running', NOW())
                RETURNING id
            """)
            res = session.execute(insert_q, {"job_id": job_id})
            session.commit()
            run_record_id = res.scalar()

            # Execute actual function
            result = func(*args, **kwargs)

            duration = (datetime.utcnow() - start_time).total_seconds()
            update_q = text("""
                UPDATE app.job_runs
                SET status = 'success',
                    finished_at = NOW(),
                    duration_seconds = :duration,
                    metadata = CAST(:meta AS JSONB)
                WHERE id = :id
            """)
            meta_json = json.dumps(result if isinstance(result, dict) else {"result": str(result)}, default=str)
            session.execute(update_q, {"duration": duration, "meta": meta_json, "id": run_record_id})
            session.commit()

        except Exception as e:
            logger.error("Job %s failed: %s", job_id, e, exc_info=True)
            if run_record_id:
                duration = (datetime.utcnow() - start_time).total_seconds()
                fail_q = text("""
                    UPDATE app.job_runs
                    SET status = 'failed',
                        finished_at = NOW(),
                        duration_seconds = :duration,
                        error_message = :err
                    WHERE id = :id
                """)
                session.execute(fail_q, {"duration": duration, "err": str(e), "id": run_record_id})
                session.commit()
        finally:
            session.close()

    def job_intraday_snapshot(self):
        """Intraday price snapshot during active trading hours."""
        if not is_market_hours():
            logger.debug("Market closed. Skipping intraday snapshot.")
            return {"skipped": True, "reason": "outside_market_hours"}

        session = SessionLocal()
        try:
            orch = IngestionOrchestrator(session)
            return orch.run_intraday_snapshot()
        finally:
            session.close()

    def job_eod_pipeline(self, target_date: date | None = None):
        """End-of-day data landing, staging, and core hypertable updates."""
        t_date = target_date or trading_date()
        logger.info("Executing EOD pipeline for %s...", t_date)
        session = SessionLocal()
        try:
            orch = IngestionOrchestrator(session)
            ingest_res = orch.run_daily_ingestion(t_date)

            builder = DailyPriceBuilder(session)
            promoted_prices = builder.process_staging_trade_summary(t_date)
            promoted_indices = builder.process_indices(t_date)

            ca_proc = CorporateActionProcessor(session)
            ca_proc.detect_from_announcements()
            ca_proc.apply_adjustment_factors()

            recon = DataReconciler(session)
            recon_report = recon.reconcile_daily(t_date)

            # Build features & update daily recommendations
            from src.features.builder import FeatureBuilder
            from src.engine.decision import DecisionEngine
            from src.alerts.telegram import TelegramAlerter

            feat_builder = FeatureBuilder(session)
            feat_builder.build_all_features(t_date)

            engine = DecisionEngine(session)
            recs = engine.run(t_date)

            alerter = TelegramAlerter()
            for r in recs[:3]:
                alerter.send_recommendation(r)

            return {
                "trading_date": str(t_date),
                "ingest": ingest_res,
                "prices_promoted": promoted_prices,
                "indices_promoted": promoted_indices,
                "reconciliation": recon_report,
                "recommendations_generated": len(recs),
            }
        finally:
            session.close()

    def catch_up(self):
        """Check for missed trading days when system was offline and run EOD catchup."""
        logger.info("Checking for missed trading days (catch-up logic)...")
        session = SessionLocal()
        try:
            query = text("""
                SELECT MAX(trading_date) FROM core.fact_price_daily
            """)
            last_date = session.execute(query).scalar()
            if not last_date:
                logger.info("No prior prices found; skipping catchup.")
                return

            today = date.today()
            # If last recorded date is earlier than today - 1 (excluding weekends)
            curr = last_date + timedelta(days=1)
            while curr < today:
                if curr.weekday() < 5:  # Monday to Friday
                    logger.info("Catching up missing trading date: %s", curr)
                    self.job_eod_pipeline(curr)
                curr += timedelta(days=1)
        except Exception as e:
            logger.warning("Catch up failed: %s", e)
        finally:
            session.close()

    def start(self):
        """Register all jobs and start APScheduler."""
        logger.info("Starting Pipeline Scheduler...")
        self.catch_up()

        # 1. Intraday snapshot every 5 min Mon-Fri 09:30 - 14:30
        self.scheduler.add_job(
            func=lambda: self._record_run("intraday_snapshot", self.job_intraday_snapshot),
            trigger=IntervalTrigger(minutes=5),
            id="intraday_snapshot",
            name="Intraday 5-min Price Snapshot",
            replace_existing=True,
        )

        # 2. Daily EOD Fetch at 14:45 Mon-Fri
        self.scheduler.add_job(
            func=lambda: self._record_run("eod_fetch", self.job_eod_pipeline),
            trigger=CronTrigger(day_of_week="mon-fri", hour=14, minute=45, timezone=COLOMBO_TZ),
            id="eod_fetch",
            name="Daily EOD Pipeline (14:45)",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("Pipeline Scheduler is active.")
