"""Connector for fetching historical OHLCV chart data from CSE."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        result = self._fetch_symbol_chart(symbol, stock_id, period, self.client)
        return self._stage_fetched_chart(symbol, stock_id, result)

    @staticmethod
    def _chart_records(data: Any) -> list[dict[str, Any]]:
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            records = data.get("chartData") or data.get("data") or []
            return records if isinstance(records, list) else []
        return []

    def _fetch_symbol_chart(
        self,
        symbol: str,
        stock_id: int | None,
        period: int,
        client: CSEApiClient,
    ) -> dict[str, Any]:
        endpoint = "chartData"
        params = {"symbol": symbol, "chartId": "CHART_BY_CLOSE", "period": str(period)}
        try:
            resp = client.post(endpoint, data=params)
            records = self._chart_records(resp.get("data"))
            status_code = resp.get("status", 200)
            elapsed_ms = resp.get("elapsed_ms", 0)
            if not records and stock_id:
                alt_endpoint = "companyChartDataByStock"
                alt_params = {"stockId": str(stock_id), "period": str(period)}
                alt_resp = client.post(alt_endpoint, data=alt_params)
                records = self._chart_records(alt_resp.get("data"))
                endpoint = alt_endpoint
                params = alt_params
                status_code = alt_resp.get("status", 200)
                elapsed_ms = alt_resp.get("elapsed_ms", elapsed_ms)
            return {
                "endpoint": endpoint,
                "params": params,
                "records": records,
                "status_code": status_code,
                "elapsed_ms": elapsed_ms,
                "error": None if records else "CSE returned no chart records",
            }
        except Exception as exc:
            return {
                "endpoint": endpoint,
                "params": params,
                "records": [],
                "status_code": None,
                "elapsed_ms": 0,
                "error": str(exc),
            }

    def _stage_fetched_chart(
        self,
        symbol: str,
        stock_id: int | None,
        result: dict[str, Any],
    ) -> int:
        records = result["records"]
        if not records:
            logger.warning("Failed to fetch chart data for %s: %s", symbol, result["error"])
            return 0

        self.lander.land(
            result["endpoint"],
            result["params"],
            records,
            result["status_code"],
            result["elapsed_ms"],
        )
        parsed_rows = parse_chart_data(symbol, stock_id, records)
        total_staged = self.dedup.upsert_chart_data(parsed_rows)
        logger.info("Staged %d chart points for %s", total_staged, symbol)
        return total_staged

    def sync_symbols(
        self,
        symbol_stock_pairs: list[tuple[str, int | None]],
        period: int = 5,
        delay: float = 0,
        max_workers: int = 4,
        progress_callback: Callable[[int, int, str, int, str | None], None] | None = None,
    ) -> dict[str, Any]:
        """Fetch chart history concurrently and stage each result on this thread."""
        run_id = self.lander.start_run("chartData")
        total_points = 0
        success_syms = 0
        failed_symbols: list[dict[str, str]] = []
        successful_symbols: list[str] = []
        total = len(symbol_stock_pairs)
        processed = 0

        def finish_symbol(sym: str, stock_id: int | None, result: dict[str, Any]) -> None:
            nonlocal processed, total_points, success_syms
            pts = self._stage_fetched_chart(sym, stock_id, result)
            processed += 1
            error = result["error"]
            if pts > 0:
                total_points += pts
                success_syms += 1
                successful_symbols.append(sym)
                error = None
            else:
                error = error or "No chart rows were staged"
                failed_symbols.append({"symbol": sym, "error": error})
            if progress_callback:
                progress_callback(processed, total, sym, pts, error)

        def fetch_with_worker_client(pair: tuple[str, int | None]) -> dict[str, Any]:
            sym, stock_id = pair
            with CSEApiClient(self.client.base_url, self.client.timeout) as client:
                return self._fetch_symbol_chart(sym, stock_id, period, client)

        if total > 1 and max_workers > 1 and type(self.client) is CSEApiClient:
            with ThreadPoolExecutor(max_workers=min(max_workers, total)) as executor:
                futures = {
                    executor.submit(fetch_with_worker_client, pair): pair
                    for pair in symbol_stock_pairs
                }
                for future in as_completed(futures):
                    sym, stock_id = futures[future]
                    try:
                        result = future.result()
                    except Exception as exc:
                        result = {
                            "endpoint": "chartData",
                            "params": {"symbol": sym},
                            "records": [],
                            "status_code": None,
                            "elapsed_ms": 0,
                            "error": str(exc),
                        }
                    finish_symbol(sym, stock_id, result)
        else:
            for sym, stock_id in symbol_stock_pairs:
                result = self._fetch_symbol_chart(sym, stock_id, period, self.client)
                finish_symbol(sym, stock_id, result)
                if delay > 0:
                    time.sleep(delay)

        self.lander.finish_run(
            run_id=run_id,
            status="success" if success_syms == total and total > 0 else "partial",
            records_fetched=total,
            records_landed=total_points,
        )

        return {
            "symbols_processed": processed,
            "symbols_succeeded": success_syms,
            "total_points": total_points,
            "successful_symbols": successful_symbols,
            "failed_symbols": failed_symbols,
        }
