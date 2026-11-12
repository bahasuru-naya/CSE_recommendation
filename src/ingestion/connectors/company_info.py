"""Connector for fetching detailed company info for CSE securities."""

from __future__ import annotations

import logging
import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.ingestion.client import CSEApiClient
from src.ingestion.raw_landing import RawLander
from src.staging.dedup import StagingDeduplicator
from src.staging.parser import parse_company_info

logger = logging.getLogger(__name__)


class CompanyInfoConnector:
    """Fetches companyInfoSummery for securities, lands raw, and populates staging.company_info."""

    def __init__(self, session: Session, client: CSEApiClient | None = None):
        self.session = session
        self.client = client or CSEApiClient()
        self.lander = RawLander(session)
        self.dedup = StagingDeduplicator(session)

    def get_candidate_symbols(self, limit: int = 100) -> list[str]:
        """Fetch active symbols from staging.trade_summary or dim_security."""
        query = text("""
            SELECT DISTINCT symbol FROM (
                SELECT symbol FROM staging.trade_summary
                UNION
                SELECT symbol FROM core.dim_security WHERE is_active = TRUE
            ) s
            ORDER BY symbol
            LIMIT :limit
        """)
        try:
            rows = self.session.execute(query, {"limit": limit}).fetchall()
            return [r[0] for r in rows if r[0]]
        except Exception:
            return ["LOLC.N0000", "COMB.N0000", "JKS.N0000", "SAMP.N0000", "HNB.N0000"]

    def sync_symbols(self, symbols: list[str] | None = None, delay: float = 0.3) -> dict[str, Any]:
        """Fetch company info for specified symbols or discovered symbols."""
        sym_list = symbols or self.get_candidate_symbols()
        endpoint = "companyInfoSummery"
        run_id = self.lander.start_run(endpoint)

        success = 0
        errors = 0

        logger.info("Starting company info sync for %d symbols...", len(sym_list))
        for sym in sym_list:
            try:
                payload = {"symbol": sym}
                resp = self.client.post(endpoint, data=payload)
                data = resp.get("data", {})
                status_code = resp.get("status_code", 200)
                elapsed_ms = resp.get("elapsed_ms", 0)

                if data:
                    self.lander.land(endpoint, payload, data, status_code, elapsed_ms)
                    parsed = parse_company_info(sym, data)
                    if self.dedup.upsert_company_info(parsed):
                        success += 1
                    else:
                        errors += 1
                else:
                    errors += 1
                time.sleep(delay)
            except Exception as e:
                errors += 1
                logger.warning("Error fetching company info for %s: %s", sym, e)

        self.lander.finish_run(
            run_id=run_id,
            status="success" if errors == 0 else "partial",
            records_fetched=len(sym_list),
            records_landed=success,
        )

        return {"status": "complete", "total": len(sym_list), "success": success, "errors": errors}
