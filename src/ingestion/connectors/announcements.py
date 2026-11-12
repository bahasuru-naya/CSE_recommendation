"""Connector for fetching corporate and regulatory announcements from CSE."""

from __future__ import annotations

from datetime import datetime
import json
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.ingestion.client import CSEApiClient
from src.ingestion.raw_landing import RawLander

logger = logging.getLogger(__name__)


class AnnouncementsConnector:
    """Fetches announcements across multiple CSE announcement categories."""

    def __init__(self, session: Session, client: CSEApiClient | None = None):
        self.session = session
        self.client = client or CSEApiClient()
        self.lander = RawLander(session)

    def sync_all(self) -> int:
        """Fetch all types of announcements and store in staging.announcements."""
        endpoints = [
            ("approvedAnnouncement", "APPROVED"),
            ("getFinancialAnnouncement", "FINANCIAL"),
            ("circularAnnouncement", "CIRCULAR"),
            ("directiveAnnouncement", "DIRECTIVE"),
            ("getNonComplianceAnnouncements", "NON_COMPLIANCE"),
            ("getBuyInBoardAnnouncements", "BUY_IN_BOARD"),
        ]

        upsert_query = text("""
            INSERT INTO staging.announcements (
                announcement_id, title, description, announcement_type,
                company_symbol, announced_date, raw_data, fetched_at, ingested_at
            ) VALUES (
                :announcement_id, :title, :description, :announcement_type,
                :company_symbol, :announced_date, CAST(:raw_data AS JSONB), NOW(), NOW()
            )
            ON CONFLICT (announcement_id) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                announcement_type = EXCLUDED.announcement_type,
                company_symbol = EXCLUDED.company_symbol,
                announced_date = EXCLUDED.announced_date,
                raw_data = EXCLUDED.raw_data,
                ingested_at = NOW()
        """)

        total_saved = 0
        for ep, ann_type in endpoints:
            try:
                resp = self.client.post(ep)
                data = resp.get("data")
                self.lander.land(ep, None, data, resp.get("status_code", 200), resp.get("elapsed_ms", 0))

                items = []
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    items = data.get("announcements") or data.get("data") or []

                for item in items:
                    ann_id = str(item.get("id") or item.get("announcementId") or f"{ann_type}_{item.get('date')}_{item.get('symbol')}")
                    title = item.get("title") or item.get("subject") or item.get("header") or ""
                    desc = item.get("description") or item.get("content") or item.get("details") or ""
                    symbol = str(item.get("symbol") or item.get("securityCode") or "").strip().upper() or None

                    # Parse date if available
                    d_raw = item.get("date") or item.get("announcedDate") or item.get("dateTime")
                    announced_dt = None
                    if isinstance(d_raw, str):
                        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M", "%d/%m/%Y"):
                            try:
                                announced_dt = datetime.strptime(d_raw[:19], fmt)
                                break
                            except ValueError:
                                continue

                    row = {
                        "announcement_id": ann_id[:50],
                        "title": title,
                        "description": desc,
                        "announcement_type": ann_type,
                        "company_symbol": symbol[:20] if symbol else None,
                        "announced_date": announced_dt or datetime.utcnow(),
                        "raw_data": json.dumps(item, default=str),
                    }
                    try:
                        self.session.execute(upsert_query, row)
                        total_saved += 1
                    except Exception as ex:
                        logger.debug("Failed saving announcement %s: %s", ann_id, ex)

                self.session.commit()
            except Exception as e:
                logger.warning("Error fetching announcement endpoint %s: %s", ep, e)

        return total_saved
