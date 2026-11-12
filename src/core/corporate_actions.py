"""Corporate actions detection and price adjustment calculations."""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class CorporateActionProcessor:
    """Detects splits, bonuses, rights and dividends, and calculates cumulative adjustment factors."""

    def __init__(self, session: Session):
        self.session = session

    def detect_from_announcements(self) -> int:
        """Scan staging.announcements for keywords: SUBDIVISION, SPLIT, BONUS, RIGHTS."""
        query = text("""
            SELECT a.announcement_id, a.company_symbol, a.title, a.description,
                   a.announced_date, s.security_id
            FROM staging.announcements a
            JOIN core.dim_security s ON s.symbol = a.company_symbol
            WHERE (
                UPPER(a.title) LIKE '%SUB-DIVISION%' OR
                UPPER(a.title) LIKE '%SPLIT%' OR
                UPPER(a.title) LIKE '%BONUS%' OR
                UPPER(a.title) LIKE '%RIGHTS%'
            )
            AND NOT EXISTS (
                SELECT 1 FROM core.fact_corporate_action ca
                WHERE ca.security_id = s.security_id
                  AND ca.ex_date = a.announced_date::date
            )
        """)
        rows = self.session.execute(query).fetchall()
        count = 0

        insert_ca = text("""
            INSERT INTO core.fact_corporate_action (
                security_id, action_type, ex_date, details, adj_factor, ingested_at
            ) VALUES (
                :security_id, :action_type, :ex_date, CAST(:details AS JSONB), :adj_factor, NOW()
            )
        """)

        for r in rows:
            ann_id, symbol, title, desc, announced_dt, sec_id = r
            action_type = "OTHER"
            adj_factor = 1.0

            text_content = f"{title} {desc}".upper()
            if "SUB-DIVISION" in text_content or "SPLIT" in text_content:
                action_type = "SPLIT"
                # Default assume 2:1 unless parsed otherwise
                adj_factor = 0.5
            elif "BONUS" in text_content:
                action_type = "BONUS"
                adj_factor = 0.909  # ~ 1 for 10
            elif "RIGHTS" in text_content:
                action_type = "RIGHTS"

            details = {"announcement_id": ann_id, "title": title}
            try:
                self.session.execute(
                    insert_ca,
                    {
                        "security_id": sec_id,
                        "action_type": action_type,
                        "ex_date": announced_dt.date() if announced_dt else None,
                        "details": json.dumps(details),
                        "adj_factor": adj_factor,
                    },
                )
                count += 1
            except Exception as e:
                logger.error("Failed recording corporate action for %s: %s", symbol, e)

        self.session.commit()
        return count

    def apply_adjustment_factors(self, security_id: int | None = None) -> int:
        """Update adj_close in core.fact_price_daily based on cumulative adjustment factors."""
        filter_clause = "WHERE security_id = :sec_id" if security_id else ""
        params = {"sec_id": security_id} if security_id else {}

        query = text(f"""
            WITH ranked_factors AS (
                SELECT security_id, ex_date, adj_factor
                FROM core.fact_corporate_action
            )
            UPDATE core.fact_price_daily p
            SET adj_factor = COALESCE((
                SELECT EXP(SUM(LN(NULLIF(ca.adj_factor, 0))))
                FROM core.fact_corporate_action ca
                WHERE ca.security_id = p.security_id
                  AND ca.ex_date > p.trading_date
            ), 1.0),
            adj_close = p.close * COALESCE((
                SELECT EXP(SUM(LN(NULLIF(ca.adj_factor, 0))))
                FROM core.fact_corporate_action ca
                WHERE ca.security_id = p.security_id
                  AND ca.ex_date > p.trading_date
            ), 1.0)
            {filter_clause};
        """)
        try:
            res = self.session.execute(query, params)
            self.session.commit()
            return res.rowcount
        except Exception as e:
            self.session.rollback()
            logger.warning("Error applying adjustment factors: %s", e)
            return 0
