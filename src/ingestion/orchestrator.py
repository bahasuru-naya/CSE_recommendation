"""Master Ingestion Orchestrator for coordinating connectors and pipeline health."""

from __future__ import annotations

from datetime import date
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.ingestion.client import CSEApiClient
from src.ingestion.connectors.announcements import AnnouncementsConnector
from src.ingestion.connectors.chart_data import ChartDataConnector
from src.ingestion.connectors.company_info import CompanyInfoConnector
from src.ingestion.connectors.market_data import MarketDataConnector
from src.ingestion.connectors.trade_summary import TradeSummaryConnector
from src.utils.time_utils import trading_date as get_trading_date

logger = logging.getLogger(__name__)


class IngestionOrchestrator:
    """Orchestrates all data ingestion connectors for the CSE pipeline."""

    def __init__(self, session: Session, client: CSEApiClient | None = None):
        self.session = session
        self.client = client or CSEApiClient()
        self.trade_summary = TradeSummaryConnector(session, self.client)
        self.company_info = CompanyInfoConnector(session, self.client)
        self.chart_data = ChartDataConnector(session, self.client)
        self.market_data = MarketDataConnector(session, self.client)
        self.announcements = AnnouncementsConnector(session, self.client)

    def run_daily_ingestion(self, target_date: date | None = None) -> dict[str, Any]:
        """Execute full daily EOD ingestion."""
        t_date = target_date or get_trading_date()
        logger.info("Executing daily EOD ingestion for %s...", t_date)

        results = {}
        # 1. Market-wide trade summary
        results["trade_summary"] = self.trade_summary.sync(t_date)

        # 2. Market indices & summary
        results["indices"] = self.market_data.sync_indices_and_summary(t_date)
        results["sectors"] = self.market_data.sync_sectors(t_date)

        # 3. Announcements
        results["announcements"] = self.announcements.sync_all()

        logger.info("Daily ingestion finished successfully for %s", t_date)
        return results

    def run_intraday_snapshot(self) -> dict[str, Any]:
        """Fast snapshot during market hours (updates prices and index)."""
        logger.info("Taking intraday market snapshot...")
        t_date = get_trading_date()
        res_trade = self.trade_summary.sync(t_date)
        res_market = self.market_data.sync_indices_and_summary(t_date)
        return {"trade_summary": res_trade, "market": res_market}

    def backfill_history(self, symbols: list[str] | None = None, period: int = 5, limit: int = 50) -> dict[str, Any]:
        """Backfill historical chart data for top symbols using their verified stock IDs.
        
        Period 5 fetches 1 full year (~245 trading days), which is the maximum available
        from the official CSE API.
        """
        pairs: list[tuple[str, int | None]] = []

        if symbols:
            # Query stock_ids for the requested symbols
            for s in symbols:
                sid = self.session.execute(
                    text("SELECT stock_id FROM core.dim_security WHERE symbol = :s"),
                    {"s": s.upper()},
                ).scalar()
                pairs.append((s.upper(), sid))
        else:
            # Select top voting common shares (.N0000) with stock_id
            rows = self.session.execute(
                text("""
                    SELECT symbol, stock_id
                    FROM core.dim_security
                    WHERE stock_id IS NOT NULL AND symbol LIKE '%.N0000'
                    ORDER BY symbol
                    LIMIT :limit
                """),
                {"limit": limit},
            ).fetchall()
            pairs = [(r[0], r[1]) for r in rows]

        if not pairs:
            # Fallback to known top liquid symbols and their stockIds
            known = {
                "LOLC.N0000": 410,
                "COMB.N0000": 208,
                "SAMP.N0000": 266,
                "HNB.N0000": 236,
                "JKH.N0000": 297,
                "DIAL.N0000": 435,
                "MELS.N0000": 393,
                "HAYL.N0000": 235,
                "ACL.N0000": 205,
                "CARG.N0000": 218,
            }
            pairs = [(s, known.get(s)) for s in (symbols or list(known.keys()))]

        logger.info("Backfilling history for %d symbols with period %d...", len(pairs), period)
        return self.chart_data.sync_symbols(pairs, period=period)

    def run_canary(self) -> dict[str, Any]:
        """Hit key CSE API endpoints to verify reachability and schema."""
        endpoints_to_test = ["marketStatus", "aspiData", "tradeSummary", "companyInfoSummery"]
        report = {}
        for ep in endpoints_to_test:
            try:
                data = {"symbol": "LOLC.N0000"} if ep == "companyInfoSummery" else None
                resp = self.client.post(ep, data=data)
                report[ep] = {
                    "status_code": resp.get("status_code"),
                    "elapsed_ms": resp.get("elapsed_ms"),
                    "ok": resp.get("status_code") == 200 and resp.get("data") is not None,
                }
            except Exception as e:
                report[ep] = {"ok": False, "error": str(e)}
        return report
