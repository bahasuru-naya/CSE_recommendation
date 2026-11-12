"""Connector for fetching and staging CSE market-wide trade summary."""

from __future__ import annotations

from datetime import date
import logging
from typing import Any

from sqlalchemy.orm import Session

from src.ingestion.client import CSEApiClient
from src.ingestion.raw_landing import RawLander
from src.staging.dedup import StagingDeduplicator
from src.staging.parser import parse_trade_summary_item
from src.utils.time_utils import trading_date as get_trading_date

logger = logging.getLogger(__name__)


class TradeSummaryConnector:
    """Fetches CSE tradeSummary, lands raw payload, parses and upserts into staging."""

    def __init__(self, session: Session, client: CSEApiClient | None = None):
        self.session = session
        self.client = client or CSEApiClient()
        self.lander = RawLander(session)
        self.dedup = StagingDeduplicator(session)

    def sync(self, target_date: date | None = None) -> dict[str, Any]:
        """Execute full fetch-and-stage workflow for trade summary."""
        endpoint = "tradeSummary"
        t_date = target_date or get_trading_date()
        run_id = self.lander.start_run(endpoint)

        try:
            logger.info("Fetching %s from CSE API...", endpoint)
            resp = self.client.post(endpoint)
            status_code = resp.get("status_code", 200)
            elapsed_ms = resp.get("elapsed_ms", 0)
            data = resp.get("data", [])

            # Handle response formats: list of stocks or nested dictionary
            records = []
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                records = data.get("reqTradeSummery") or data.get("tradeSummary") or data.get("data") or []

            # 1. Land raw
            self.lander.land(endpoint, None, data, status_code, elapsed_ms)

            # 2. Parse items
            parsed_rows = [parse_trade_summary_item(item, default_trading_date=t_date) for item in records]

            # 3. Upsert to staging
            success, errors = self.dedup.upsert_trade_summary(parsed_rows)

            self.lander.finish_run(
                run_id=run_id,
                status="success" if errors == 0 else "partial",
                records_fetched=len(records),
                records_landed=success,
            )

            logger.info("Trade summary sync complete: %d parsed, %d staged, %d errors", len(records), success, errors)
            return {"status": "success", "fetched": len(records), "staged": success, "errors": errors}

        except Exception as e:
            logger.error("Trade summary sync failed: %s", e, exc_info=True)
            self.lander.finish_run(run_id=run_id, status="failed", error_message=str(e))
            raise
