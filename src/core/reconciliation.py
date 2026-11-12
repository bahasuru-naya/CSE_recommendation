"""Data reconciliation, quality audits, freshness validation, and anomaly checks."""

from __future__ import annotations

from datetime import date, datetime
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.utils.time_utils import trading_date as get_trading_date

logger = logging.getLogger(__name__)


class DataReconciler:
    """Performs daily quality audits across staging and core data."""

    def __init__(self, session: Session):
        self.session = session

    def reconcile_daily(self, target_date: date | None = None) -> dict[str, Any]:
        """Run standard reconciliation checks for target date."""
        t_date = target_date or get_trading_date()
        logger.info("Running reconciliation checks for %s...", t_date)

        # 1. Total volume & turnover check
        query_totals = text("""
            SELECT
                COUNT(*) AS security_count,
                SUM(volume) AS total_volume,
                SUM(turnover) AS total_turnover
            FROM core.fact_price_daily
            WHERE trading_date = :t_date
        """)
        row = self.session.execute(query_totals, {"t_date": t_date}).fetchone()

        # 2. Check market summary totals
        query_mkt = text("""
            SELECT total_volume, total_turnover
            FROM staging.market_summary
            WHERE trading_date = :t_date
        """)
        mkt_row = self.session.execute(query_mkt, {"t_date": t_date}).fetchone()

        # 3. Discrepancies between staging.trade_summary and staging.chart_data close
        query_diff = text("""
            SELECT t.symbol, t.last_traded_price AS trade_close, c.close_price AS chart_close,
                   ABS(t.last_traded_price - c.close_price) AS diff
            FROM staging.trade_summary t
            JOIN staging.chart_data c
              ON t.symbol = c.symbol AND t.trading_date = c.trading_date
            WHERE t.trading_date = :t_date
              AND ABS(t.last_traded_price - c.close_price) > 0.05
            LIMIT 10
        """)
        diff_rows = self.session.execute(query_diff, {"t_date": t_date}).fetchall()
        discrepancies = [{"symbol": r[0], "trade_close": float(r[1]), "chart_close": float(r[2]), "diff": float(r[3])} for r in diff_rows]

        report = {
            "trading_date": str(t_date),
            "securities_recorded": row[0] if row else 0,
            "fact_volume": int(row[1] or 0) if row else 0,
            "fact_turnover": float(row[2] or 0.0) if row else 0.0,
            "market_summary_volume": int(mkt_row[0] or 0) if mkt_row else None,
            "market_summary_turnover": float(mkt_row[1] or 0.0) if mkt_row else None,
            "discrepancies_count": len(discrepancies),
            "discrepancies_sample": discrepancies,
            "status": "PASSED" if len(discrepancies) == 0 else "WARNING",
        }
        return report

    def check_freshness(self) -> dict[str, Any]:
        """Check when each core table was last updated."""
        query = text("""
            SELECT
                'fact_price_daily' AS table_name,
                MAX(trading_date) AS latest_date,
                MAX(ingested_at) AS latest_ingest
            FROM core.fact_price_daily
            UNION ALL
            SELECT
                'fact_index_daily',
                MAX(trading_date),
                NULL
            FROM core.fact_index_daily
            UNION ALL
            SELECT
                'staging.trade_summary',
                MAX(trading_date),
                MAX(ingested_at)
            FROM staging.trade_summary
        """)
        rows = self.session.execute(query).fetchall()
        freshness = {}
        for r in rows:
            freshness[r[0]] = {
                "latest_date": str(r[1]) if r[1] else None,
                "latest_ingest": str(r[2]) if r[2] else None,
            }

        # Check staleness: if latest date in price daily is more than 3 calendar days ago
        price_latest = freshness.get("fact_price_daily", {}).get("latest_date")
        is_stale = False
        if price_latest:
            try:
                p_dt = datetime.strptime(price_latest, "%Y-%m-%d").date()
                if (date.today() - p_dt).days > 3:
                    is_stale = True
            except Exception:
                pass

        return {"tables": freshness, "is_stale": is_stale, "checked_at": datetime.utcnow().isoformat()}

    def detect_anomalies(self, threshold_pct: float = 0.25) -> list[dict[str, Any]]:
        """Find unexplained overnight jumps (> 25% change without corporate action)."""
        query = text("""
            SELECT s.symbol, p.trading_date, p.close, p.previous_close, p.change_pct
            FROM core.fact_price_daily p
            JOIN core.dim_security s ON s.security_id = p.security_id
            WHERE ABS(p.change_pct) >= :threshold
              AND p.trading_date >= CURRENT_DATE - INTERVAL '14 days'
            ORDER BY p.trading_date DESC, ABS(p.change_pct) DESC
            LIMIT 20
        """)
        rows = self.session.execute(query, {"threshold": threshold_pct * 100}).fetchall()
        return [
            {
                "symbol": r[0],
                "trading_date": str(r[1]),
                "close": float(r[2]) if r[2] else None,
                "previous_close": float(r[3]) if r[3] else None,
                "change_pct": float(r[4]) if r[4] else None,
            }
            for r in rows
        ]
