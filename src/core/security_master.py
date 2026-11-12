"""Security Master: builds and maintains the core.dim_security dimension table."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SecurityMasterBuilder:
    """Synchronizes dim_security with data discovered across staging tables."""

    def __init__(self, session: Session):
        self.session = session

    def rebuild_from_staging(self) -> int:
        """Scan staging.trade_summary, staging.company_info, and raw payloads to upsert core.dim_security."""
        logger.info("Synchronizing core.dim_security from staging...")

        upsert_query = text("""
            INSERT INTO core.dim_security (
                symbol, name, isin, sector, industry, is_active,
                share_type, shares_outstanding, stock_id, created_at, updated_at
            )
            SELECT
                s.symbol,
                COALESCE(ci.name, s.name) AS name,
                ci.isin,
                ci.sector,
                ci.industry,
                TRUE AS is_active,
                CASE
                    WHEN s.symbol LIKE '%.N0000' THEN 'VOTING_COMMON'
                    WHEN s.symbol LIKE '%.X0000' THEN 'NON_VOTING'
                    ELSE 'OTHER'
                END AS share_type,
                ci.shares_outstanding,
                COALESCE(
                    (
                        SELECT (elem->>'id')::int
                        FROM raw.api_payloads p,
                        jsonb_array_elements(
                            CASE
                                WHEN jsonb_typeof(p.response_payload) = 'array' THEN p.response_payload
                                WHEN p.response_payload ? 'reqTradeSummery' THEN p.response_payload->'reqTradeSummery'
                                ELSE '[]'::jsonb
                            END
                        ) elem
                        WHERE p.endpoint = 'tradeSummary' AND elem->>'symbol' = s.symbol
                        ORDER BY p.fetched_at DESC LIMIT 1
                    ),
                    NULL
                ) AS stock_id,
                NOW(),
                NOW()
            FROM (
                SELECT symbol, name, MAX(trading_date) AS last_seen
                FROM staging.trade_summary
                GROUP BY symbol, name
            ) s
            LEFT JOIN LATERAL (
                SELECT name, isin, sector, industry, shares_outstanding
                FROM staging.company_info
                WHERE symbol = s.symbol
                ORDER BY fetched_at DESC
                LIMIT 1
            ) ci ON TRUE
            ON CONFLICT (symbol) DO UPDATE SET
                name = COALESCE(EXCLUDED.name, core.dim_security.name),
                isin = COALESCE(EXCLUDED.isin, core.dim_security.isin),
                sector = COALESCE(EXCLUDED.sector, core.dim_security.sector),
                industry = COALESCE(EXCLUDED.industry, core.dim_security.industry),
                shares_outstanding = COALESCE(EXCLUDED.shares_outstanding, core.dim_security.shares_outstanding),
                stock_id = COALESCE(EXCLUDED.stock_id, core.dim_security.stock_id),
                is_active = TRUE,
                updated_at = NOW();
        """)
        result = self.session.execute(upsert_query)
        self.session.commit()
        count = result.rowcount
        logger.info("Updated %d securities in dim_security", count)
        return count

    def get_security_id(self, symbol: str) -> int:
        """Fetch security_id for symbol or insert a new record if missing."""
        sym = symbol.strip().upper()
        row = self.session.execute(
            text("SELECT security_id FROM core.dim_security WHERE symbol = :symbol"),
            {"symbol": sym},
        ).fetchone()

        if row:
            return row[0]

        res = self.session.execute(
            text("""
                INSERT INTO core.dim_security (symbol, is_active, share_type)
                VALUES (
                    :symbol, TRUE,
                    CASE WHEN :symbol LIKE '%.N0000' THEN 'VOTING_COMMON' ELSE 'OTHER' END
                )
                RETURNING security_id
            """),
            {"symbol": sym},
        )
        self.session.commit()
        return res.scalar()

    def get_active_symbols(self, common_only: bool = True) -> list[dict[str, Any]]:
        """Return list of active securities."""
        condition = "WHERE is_active = TRUE"
        if common_only:
            condition += " AND symbol LIKE '%.N0000'"

        query = text(f"""
            SELECT security_id, symbol, name, sector, shares_outstanding, stock_id
            FROM core.dim_security
            {condition}
            ORDER BY symbol
        """)
        rows = self.session.execute(query).fetchall()
        return [
            {
                "security_id": r[0],
                "symbol": r[1],
                "name": r[2],
                "sector": r[3],
                "shares_outstanding": r[4],
                "stock_id": r[5],
            }
            for r in rows
        ]
