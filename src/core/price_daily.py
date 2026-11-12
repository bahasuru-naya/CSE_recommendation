"""Daily price transformation: merges staging tables into core.fact_price_daily."""

from __future__ import annotations

from datetime import date
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.security_master import SecurityMasterBuilder
from src.utils.time_utils import trading_date as get_trading_date

logger = logging.getLogger(__name__)


class DailyPriceBuilder:
    """Transforms staging data into core.fact_price_daily and core.fact_index_daily."""

    def __init__(self, session: Session):
        self.session = session
        self.sec_master = SecurityMasterBuilder(session)

    def process_staging_trade_summary(self, target_date: date | None = None) -> int:
        """Promote staging.trade_summary rows to core.fact_price_daily for target date."""
        t_date = target_date or get_trading_date()
        logger.info("Promoting staging.trade_summary to core.fact_price_daily for %s...", t_date)

        # First ensure all securities exist in dim_security
        self.sec_master.rebuild_from_staging()

        query = text("""
            INSERT INTO core.fact_price_daily (
                security_id, trading_date, open, high, low, close,
                volume, turnover, num_trades, change, change_pct,
                previous_close, is_traded, data_source, ingested_at, as_of_date,
                adj_close, adj_factor
            )
            SELECT
                s.security_id,
                t.trading_date,
                t.open_price,
                t.high,
                t.low,
                t.last_traded_price,
                COALESCE(t.volume, 0),
                COALESCE(t.turnover, 0),
                COALESCE(t.num_trades, 0),
                t.change,
                t.change_percentage,
                t.previous_close,
                CASE WHEN COALESCE(t.volume, 0) > 0 THEN TRUE ELSE FALSE END,
                'trade_summary',
                NOW(),
                t.trading_date,
                t.last_traded_price,
                1.0
            FROM staging.trade_summary t
            JOIN core.dim_security s ON s.symbol = t.symbol
            WHERE t.trading_date = :target_date
            ON CONFLICT (security_id, trading_date) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                turnover = EXCLUDED.turnover,
                num_trades = EXCLUDED.num_trades,
                change = EXCLUDED.change,
                change_pct = EXCLUDED.change_pct,
                previous_close = EXCLUDED.previous_close,
                is_traded = EXCLUDED.is_traded,
                data_source = EXCLUDED.data_source,
                ingested_at = NOW(),
                adj_close = EXCLUDED.close
        """)

        result = self.session.execute(query, {"target_date": t_date})
        self.session.commit()
        count = result.rowcount
        logger.info("Upserted %d rows into core.fact_price_daily for %s", count, t_date)
        return count

    def process_staging_chart_data(self) -> int:
        """Promote historical staging.chart_data into core.fact_price_daily."""
        logger.info("Promoting staging.chart_data to core.fact_price_daily...")
        self.sec_master.rebuild_from_staging()

        query = text("""
            INSERT INTO core.fact_price_daily (
                security_id, trading_date, open, high, low, close,
                volume, turnover, num_trades, is_traded, data_source,
                ingested_at, as_of_date, adj_close, adj_factor
            )
            SELECT
                s.security_id,
                c.trading_date,
                c.open_price,
                c.high,
                c.low,
                c.close_price,
                COALESCE(c.volume, 0),
                COALESCE(c.turnover, 0),
                COALESCE(c.num_trades, 0),
                CASE WHEN COALESCE(c.volume, 0) > 0 THEN TRUE ELSE FALSE END,
                'chart_data',
                NOW(),
                c.trading_date,
                c.close_price,
                1.0
            FROM staging.chart_data c
            JOIN core.dim_security s ON s.symbol = c.symbol
            ON CONFLICT (security_id, trading_date) DO UPDATE SET
                open = COALESCE(core.fact_price_daily.open, EXCLUDED.open),
                high = COALESCE(core.fact_price_daily.high, EXCLUDED.high),
                low = COALESCE(core.fact_price_daily.low, EXCLUDED.low),
                close = COALESCE(core.fact_price_daily.close, EXCLUDED.close),
                volume = GREATEST(COALESCE(core.fact_price_daily.volume, 0), EXCLUDED.volume),
                turnover = GREATEST(COALESCE(core.fact_price_daily.turnover, 0), EXCLUDED.turnover),
                is_traded = (EXCLUDED.volume > 0)
        """)
        result = self.session.execute(query)
        self.session.commit()
        count = result.rowcount
        logger.info("Upserted %d historical points into fact_price_daily", count)
        return count

    def process_indices(self, target_date: date | None = None) -> int:
        """Promote staging.market_summary into core.fact_index_daily for ASPI and S&P SL20."""
        t_date = target_date or get_trading_date()
        query = text("""
            INSERT INTO core.fact_index_daily (
                index_name, trading_date, close, change, change_pct, turnover, volume, num_trades
            )
            SELECT
                'ASPI' AS index_name,
                trading_date,
                aspi_value,
                aspi_change,
                aspi_change_pct,
                total_turnover,
                total_volume,
                total_trades
            FROM staging.market_summary
            WHERE trading_date = :target_date AND aspi_value IS NOT NULL
            UNION ALL
            SELECT
                'S&P SL20' AS index_name,
                trading_date,
                snp_value,
                snp_change,
                snp_change_pct,
                NULL, NULL, NULL
            FROM staging.market_summary
            WHERE trading_date = :target_date AND snp_value IS NOT NULL
            ON CONFLICT (index_name, trading_date) DO UPDATE SET
                close = EXCLUDED.close,
                change = EXCLUDED.change,
                change_pct = EXCLUDED.change_pct,
                turnover = COALESCE(EXCLUDED.turnover, core.fact_index_daily.turnover),
                volume = COALESCE(EXCLUDED.volume, core.fact_index_daily.volume),
                num_trades = COALESCE(EXCLUDED.num_trades, core.fact_index_daily.num_trades)
        """)
        result = self.session.execute(query, {"target_date": t_date})
        self.session.commit()
        return result.rowcount
