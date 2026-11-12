"""Connector for fetching index and overall market summary data from CSE."""

from __future__ import annotations

from datetime import date
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.ingestion.client import CSEApiClient
from src.ingestion.raw_landing import RawLander
from src.staging.dedup import StagingDeduplicator
from src.staging.parser import parse_market_summary, safe_float, safe_int
from src.utils.time_utils import trading_date as get_trading_date

logger = logging.getLogger(__name__)


class MarketDataConnector:
    """Fetches ASPI, S&P SL20, and daily market summaries."""

    def __init__(self, session: Session, client: CSEApiClient | None = None):
        self.session = session
        self.client = client or CSEApiClient()
        self.lander = RawLander(session)
        self.dedup = StagingDeduplicator(session)

    def sync_indices_and_summary(self, target_date: date | None = None) -> dict[str, Any]:
        """Fetch aspiData, snpData, marketSummery and upsert into staging.market_summary."""
        t_date = target_date or get_trading_date()

        # 1. ASPI
        aspi_resp = self.client.post("aspiData")
        aspi_data = aspi_resp.get("data", {})
        self.lander.land("aspiData", None, aspi_data, aspi_resp.get("status_code", 200), aspi_resp.get("elapsed_ms", 0))

        # 2. S&P SL20
        snp_resp = self.client.post("snpData")
        snp_data = snp_resp.get("data", {})
        self.lander.land("snpData", None, snp_data, snp_resp.get("status_code", 200), snp_resp.get("elapsed_ms", 0))

        # 3. Market Summary
        summ_resp = self.client.post("marketSummery")
        summ_data = summ_resp.get("data", {})
        self.lander.land("marketSummery", None, summ_data, summ_resp.get("status_code", 200), summ_resp.get("elapsed_ms", 0))

        # 4. Parse & Upsert
        parsed = parse_market_summary(
            trading_date=t_date,
            aspi_data=aspi_data if isinstance(aspi_data, dict) else {},
            snp_data=snp_data if isinstance(snp_data, dict) else {},
            summary_data=summ_data if isinstance(summ_data, dict) else {},
        )
        success = self.dedup.upsert_market_summary(parsed)

        return {"status": "success" if success else "failed", "trading_date": t_date, "data": parsed}

    def sync_sectors(self, target_date: date | None = None) -> int:
        """Fetch allSectors and upsert into staging.sector_data."""
        t_date = target_date or get_trading_date()
        resp = self.client.post("allSectors")
        data = resp.get("data", [])
        self.lander.land("allSectors", None, data, resp.get("status_code", 200), resp.get("elapsed_ms", 0))

        sectors = []
        if isinstance(data, list):
            sectors = data
        elif isinstance(data, dict):
            sectors = data.get("allSectors") or data.get("sectors") or []

        query = text("""
            INSERT INTO staging.sector_data (
                sector_name, index_value, change, change_pct, volume, turnover,
                trading_date, fetched_at, ingested_at
            ) VALUES (
                :sector_name, :index_value, :change, :change_pct, :volume, :turnover,
                :trading_date, NOW(), NOW()
            )
            ON CONFLICT (sector_name, trading_date) DO UPDATE SET
                index_value = EXCLUDED.index_value,
                change = EXCLUDED.change,
                change_pct = EXCLUDED.change_pct,
                volume = EXCLUDED.volume,
                turnover = EXCLUDED.turnover,
                fetched_at = EXCLUDED.fetched_at,
                ingested_at = NOW()
        """)

        saved = 0
        for s in sectors:
            name = s.get("sector") or s.get("sectorName") or s.get("name")
            if not name:
                continue
            row = {
                "sector_name": str(name).strip(),
                "index_value": safe_float(s.get("indexValue") or s.get("value")),
                "change": safe_float(s.get("change")),
                "change_pct": safe_float(s.get("percentage") or s.get("changePercentage")),
                "volume": safe_int(s.get("volume")),
                "turnover": safe_float(s.get("turnover")),
                "trading_date": t_date,
            }
            try:
                self.session.execute(query, row)
                saved += 1
            except Exception as e:
                logger.warning("Error saving sector %s: %s", name, e)

        self.session.commit()
        return saved
