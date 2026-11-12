"""Deduplication and idempotent upsert utilities for the staging layer."""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class StagingDeduplicator:
    """Manages idempotent upserts into staging layer tables."""

    def __init__(self, session: Session):
        self.session = session

    def upsert_trade_summary(self, rows: list[dict[str, Any]]) -> tuple[int, int]:
        """Upsert records into staging.trade_summary.

        Returns (inserted_or_updated_count, error_count).
        """
        if not rows:
            return 0, 0

        query = text("""
            INSERT INTO staging.trade_summary (
                symbol, name, last_traded_price, change, change_percentage,
                volume, turnover, high, low, open_price, previous_close,
                num_trades, market_cap, trading_date, fetched_at, ingested_at
            ) VALUES (
                :symbol, :name, :last_traded_price, :change, :change_percentage,
                :volume, :turnover, :high, :low, :open_price, :previous_close,
                :num_trades, :market_cap, :trading_date, NOW(), NOW()
            )
            ON CONFLICT (symbol, trading_date) DO UPDATE SET
                name = EXCLUDED.name,
                last_traded_price = EXCLUDED.last_traded_price,
                change = EXCLUDED.change,
                change_percentage = EXCLUDED.change_percentage,
                volume = EXCLUDED.volume,
                turnover = EXCLUDED.turnover,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                open_price = EXCLUDED.open_price,
                previous_close = EXCLUDED.previous_close,
                num_trades = EXCLUDED.num_trades,
                market_cap = EXCLUDED.market_cap,
                fetched_at = EXCLUDED.fetched_at,
                ingested_at = NOW()
        """)

        success = 0
        errors = 0
        for r in rows:
            if not r.get("symbol"):
                continue
            try:
                self.session.execute(query, r)
                success += 1
            except Exception as e:
                errors += 1
                logger.error("Failed to upsert trade summary for %s: %s", r.get("symbol"), e)

        self.session.commit()
        return success, errors

    def upsert_company_info(self, info: dict[str, Any]) -> bool:
        """Upsert a record into staging.company_info."""
        query = text("""
            INSERT INTO staging.company_info (
                symbol, name, isin, sector, industry, market_cap,
                last_traded_price, change, change_percentage,
                beta_spsl, beta_aspi, shares_outstanding, listed_date,
                raw_data, fetched_at, fetched_date, ingested_at
            ) VALUES (
                :symbol, :name, :isin, :sector, :industry, :market_cap,
                :last_traded_price, :change, :change_percentage,
                :beta_spsl, :beta_aspi, :shares_outstanding, :listed_date,
                CAST(:raw_data AS JSONB), NOW(), CURRENT_DATE, NOW()
            )
            ON CONFLICT (symbol, fetched_date) DO UPDATE SET
                name = EXCLUDED.name,
                isin = EXCLUDED.isin,
                sector = EXCLUDED.sector,
                industry = EXCLUDED.industry,
                market_cap = EXCLUDED.market_cap,
                last_traded_price = EXCLUDED.last_traded_price,
                change = EXCLUDED.change,
                change_percentage = EXCLUDED.change_percentage,
                beta_spsl = EXCLUDED.beta_spsl,
                beta_aspi = EXCLUDED.beta_aspi,
                shares_outstanding = EXCLUDED.shares_outstanding,
                raw_data = EXCLUDED.raw_data,
                ingested_at = NOW()
        """)
        try:
            params = {**info, "raw_data": json.dumps(info.get("raw_data") or {}, default=str)}
            self.session.execute(query, params)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            logger.error("Failed to upsert company info for %s: %s", info.get("symbol"), e)
            return False

    def upsert_chart_data(self, rows: list[dict[str, Any]]) -> int:
        """Upsert historical chart rows into staging.chart_data."""
        if not rows:
            return 0

        query = text("""
            INSERT INTO staging.chart_data (
                symbol, stock_id, trading_date, open_price, high, low,
                close_price, volume, turnover, num_trades, fetched_at, ingested_at
            ) VALUES (
                :symbol, :stock_id, :trading_date, :open_price, :high, :low,
                :close_price, :volume, :turnover, :num_trades, NOW(), NOW()
            )
            ON CONFLICT (symbol, trading_date) DO UPDATE SET
                stock_id = COALESCE(EXCLUDED.stock_id, staging.chart_data.stock_id),
                open_price = EXCLUDED.open_price,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close_price = EXCLUDED.close_price,
                volume = EXCLUDED.volume,
                turnover = EXCLUDED.turnover,
                num_trades = EXCLUDED.num_trades,
                ingested_at = NOW()
        """)
        count = 0
        for r in rows:
            try:
                self.session.execute(query, r)
                count += 1
            except Exception as e:
                logger.error("Failed to upsert chart point (%s, %s): %s", r.get("symbol"), r.get("trading_date"), e)
        self.session.commit()
        return count

    def upsert_market_summary(self, data: dict[str, Any]) -> bool:
        """Upsert daily market summary into staging.market_summary."""
        query = text("""
            INSERT INTO staging.market_summary (
                trading_date, aspi_value, aspi_change, aspi_change_pct,
                snp_value, snp_change, snp_change_pct, total_turnover,
                total_volume, total_trades, market_cap, fetched_at, ingested_at
            ) VALUES (
                :trading_date, :aspi_value, :aspi_change, :aspi_change_pct,
                :snp_value, :snp_change, :snp_change_pct, :total_turnover,
                :total_volume, :total_trades, :market_cap, NOW(), NOW()
            )
            ON CONFLICT (trading_date) DO UPDATE SET
                aspi_value = EXCLUDED.aspi_value,
                aspi_change = EXCLUDED.aspi_change,
                aspi_change_pct = EXCLUDED.aspi_change_pct,
                snp_value = EXCLUDED.snp_value,
                snp_change = EXCLUDED.snp_change,
                snp_change_pct = EXCLUDED.snp_change_pct,
                total_turnover = EXCLUDED.total_turnover,
                total_volume = EXCLUDED.total_volume,
                total_trades = EXCLUDED.total_trades,
                market_cap = EXCLUDED.market_cap,
                fetched_at = EXCLUDED.fetched_at,
                ingested_at = NOW()
        """)
        try:
            self.session.execute(query, data)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            logger.error("Failed to upsert market summary: %s", e)
            return False
