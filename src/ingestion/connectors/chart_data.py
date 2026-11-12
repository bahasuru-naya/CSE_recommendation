"""Connector for fetching historical OHLCV chart data from CSE."""

from __future__ import annotations

import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from src.ingestion.client import CSEApiClient
from src.ingestion.raw_landing import RawLander
from src.staging.dedup import StagingDeduplicator
from src.staging.parser import parse_chart_data

logger = logging.getLogger(__name__)


class ChartDataConnector:
    """Fetches chartData or companyChartDataByStock for backfill and historical series."""

    def __init__(self, session: Session, client: CSEApiClient | None = None):
        self.session = session
        self.client = client or CSEApiClient()
        self.lander = RawLander(session)
        self.dedup = StagingDeduplicator(session)

    def sync_symbol_chart(
        self,
        symbol: str,
        stock_id: int | None = None,
        period: int = 5,  # default 1 year (max CSE API history)
    ) -> int:
        """Fetch chart data for a single symbol using chartData or companyChartDataByStock."""
        endpoint = "chartData"
        params = {"symbol": symbol, "chartId": "CHART_BY_CLOSE", "period": str(period)}
        total_staged = 0

        try:
            resp = self.client.post(endpoint, data=params)
            data = resp.get("data")
            status_code = resp.get("status_code", 200)
            elapsed_ms = resp.get("elapsed_ms", 0)

            # Fallback to companyChartDataByStock if stock_id is provided and chartData empty
            records = []
            if isinstance(data, list) and data:
                records = data
            elif isinstance(data, dict):
                records = data.get("chartData") or data.get("data") or []

            if not records and stock_id:
                alt_endpoint = "companyChartDataByStock"
                alt_params = {"stockId": str(stock_id), "period": str(period)}
                alt_resp = self.client.post(alt_endpoint, data=alt_params)
                alt_data = alt_resp.get("data")
                if isinstance(alt_data, list):
                    records = alt_data
                elif isinstance(alt_data, dict):
                    records = alt_data.get("chartData") or alt_data.get("data") or []
                endpoint = alt_endpoint
                params = alt_params

            if records:
                self.lander.land(endpoint, params, records, status_code, elapsed_ms)
                parsed_rows = parse_chart_data(symbol, stock_id, records)
                total_staged = self.dedup.upsert_chart_data(parsed_rows)
                logger.info("Staged %d chart points for %s", total_staged, symbol)

        except Exception as e:
            logger.warning("Failed to fetch chart data for %s: %s", symbol, e)

        return total_staged

    def sync_symbols(self, symbol_stock_pairs: list[tuple[str, int | None]], period: int = 5, delay: float = 0.5) -> dict[str, Any]:
        """Fetch chart history for multiple securities."""
        run_id = self.lander.start_run("chartData")
        total_points = 0
        success_syms = 0

        for sym, stock_id in symbol_stock_pairs:
            pts = self.sync_symbol_chart(sym, stock_id, period)
            if pts > 0:
                total_points += pts
                success_syms += 1
            time.sleep(delay)

        self.lander.finish_run(
            run_id=run_id,
            status="success" if success_syms > 0 else "partial",
            records_fetched=len(symbol_stock_pairs),
            records_landed=total_points,
        )

        return {"symbols_processed": len(symbol_stock_pairs), "symbols_succeeded": success_syms, "total_points": total_points}
