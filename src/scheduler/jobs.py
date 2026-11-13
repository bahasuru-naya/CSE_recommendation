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
        self._last_telegram_alert_slot: tuple[date, str] | None = None

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

    def _register_job_records(self):
        """Create the database rows required by job-run tracking."""
        jobs = (
            ("intraday_snapshot", "Intraday Price Snapshot", "interval_5m"),
            ("eod_fetch", "EOD Ingestion & Recommendations", "cron_14:45"),
            ("telegram_alerts", "Daily Telegram Alerts", "daily"),
        )
        session = SessionLocal()
        try:
            for job_id, name, schedule_type in jobs:
                session.execute(
                    text("""
                        INSERT INTO app.jobs (job_id, job_name, schedule_type)
                        VALUES (:job_id, :name, :schedule_type)
                        ON CONFLICT (job_id) DO NOTHING
                    """),
                    {"job_id": job_id, "name": name, "schedule_type": schedule_type},
                )
            session.commit()
        except Exception:
            session.rollback()
            logger.exception("Could not register scheduled jobs.")
            raise
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

            feat_builder = FeatureBuilder(session)
            feat_builder.build_all_features(t_date)

            engine = DecisionEngine(session)
            recs = engine.run(t_date)

            # Filter out kill-switch warning dicts (not real recommendations)
            real_recs = [r for r in recs if not (isinstance(r, dict) and "warning" in r)]

            return {
                "trading_date": str(t_date),
                "ingest": ingest_res,
                "prices_promoted": promoted_prices,
                "indices_promoted": promoted_indices,
                "reconciliation": recon_report,
                "recommendations_generated": len(real_recs),
            }
        finally:
            session.close()

    def job_telegram_alerts(self):
        """Send the latest recommendations for the current trading date."""
        from src.alerts.telegram import TelegramAlerter

        session = SessionLocal()
        try:
            recommendations = session.execute(
                text("""
                    SELECT signal, symbol, security_name, confidence, entry_price_low,
                           entry_price_high, stop_loss, target_price, max_quantity,
                           position_size_pct, horizon_days
                    FROM app.recommendations
                    WHERE recommendation_date = :trading_date AND status = 'active'
                    ORDER BY confidence DESC NULLS LAST
                    LIMIT 3
                """),
                {"trading_date": trading_date()},
            ).mappings().all()
            if not recommendations:
                logger.info("No current recommendations to send to Telegram.")
                return {"sent": 0, "reason": "no_recommendations"}

            alerter = TelegramAlerter(db=session)
            failed = sum(not alerter.send_recommendation(dict(rec)) for rec in recommendations)
            if failed:
                raise RuntimeError(f"Telegram failed to send {failed} recommendation alert(s).")
            return {"sent": len(recommendations)}
        finally:
            session.close()

    def _check_telegram_alert_schedule(self):
        """Check the persisted daily alert time and run alerts when it matches."""
        now = datetime.now(COLOMBO_TZ)
        if now.weekday() >= 5:
            return

        session = SessionLocal()
        try:
            value = session.execute(
                text("SELECT value FROM app.settings WHERE key = 'telegram'")
            ).scalar()
        finally:
            session.close()

        alert_time = value.get("alert_time", "15:00") if isinstance(value, dict) else "15:00"
        slot = (now.date(), alert_time)
        if (
            self._last_telegram_alert_slot == slot
            or (
                isinstance(value, dict)
                and value.get("last_sent_date") == now.date().isoformat()
                and value.get("last_sent_time") == alert_time
            )
        ):
            return
        if now.strftime("%H:%M") < alert_time:
            return

        session = SessionLocal()
        try:
            has_recommendations = bool(
                session.execute(
                    text("""
                        SELECT EXISTS (
                            SELECT 1 FROM app.recommendations
                            WHERE recommendation_date = :trading_date AND status = 'active'
                        )
                    """),
                    {"trading_date": trading_date(now)},
                ).scalar()
            )
        finally:
            session.close()
        if not has_recommendations:
            return

        self._last_telegram_alert_slot = slot
        try:
            result = self.job_telegram_alerts()
            logger.info("Scheduled Telegram alerts completed: %s", result)
            if result.get("sent", 0):
                session = SessionLocal()
                try:
                    value = dict(value) if isinstance(value, dict) else {}
                    value["last_sent_date"] = now.date().isoformat()
                    value["last_sent_time"] = alert_time
                    session.execute(
                        text("""
                            UPDATE app.settings
                            SET value = CAST(:value AS JSONB), updated_at = NOW()
                            WHERE key = 'telegram'
                        """),
                        {"value": json.dumps(value)},
                    )
                    session.commit()
                finally:
                    session.close()
        except Exception:
            logger.exception("Scheduled Telegram alerts failed.")

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
        self._register_job_records()
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

        self.scheduler.add_job(
            func=self._check_telegram_alert_schedule,
            trigger=CronTrigger(minute="*", timezone=COLOMBO_TZ),
            id="telegram_alert_clock",
            name="Check Telegram Alert Schedule",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("Pipeline Scheduler is active.")

    def stop(self):
        """Stop the background scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
