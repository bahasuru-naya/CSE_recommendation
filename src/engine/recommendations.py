"""Recommendations manager: persistence and lifecycle in app.recommendations."""

from __future__ import annotations

import json
import logging
import math
from datetime import date, datetime, timedelta
from numbers import Integral, Real
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, Real):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


class RecommendationManager:
    """Saves, queries, and updates recommendation lifecycle states."""

    def __init__(self, session: Session):
        self.session = session

    def save_recommendations(self, recs: list[dict[str, Any]]) -> int:
        """Persist recommendations to app.recommendations.

        Only stores the latest predictions, automatically purging older historical
        predictions and removing any duplicate predictions per stock symbol.
        """
        if not recs:
            return 0

        # 1. Deduplicate incoming recommendations by symbol (retain highest confidence)
        unique_recs: dict[str, dict[str, Any]] = {}
        for r in recs:
            sym = (r.get("symbol") or "").strip().upper()
            if not sym:
                continue
            prev = unique_recs.get(sym)
            if not prev or float(r.get("confidence") or 0.0) > float(prev.get("confidence") or 0.0):
                unique_recs[sym] = r

        deduped = list(unique_recs.values())
        if not deduped:
            return 0

        # 2. Determine latest recommendation date in this batch
        latest_date = max(r.get("recommendation_date") or date.today() for r in deduped)
        symbols = list(unique_recs.keys())

        insert_q = text("""
            INSERT INTO app.recommendations (
                security_id, symbol, security_name, recommendation_date,
                signal, confidence, entry_price_low, entry_price_high,
                stop_loss, target_price, position_size_pct, max_quantity,
                horizon_days, reasons, model_version, data_freshness,
                logo_url, expires_at, status, created_at
            ) VALUES (
                :security_id, :symbol, :security_name, :recommendation_date,
                :signal, :confidence, :entry_price_low, :entry_price_high,
                :stop_loss, :target_price, :position_size_pct, :max_quantity,
                :horizon_days, CAST(:reasons AS JSONB), :model_version, CAST(:data_freshness AS JSONB),
                :logo_url, :expires_at, 'active', NOW()
            )
        """)

        insert_params = []
        for r in deduped:
            horizon_days = r.get("horizon_days", 10)
            insert_params.append({
                "security_id": r["security_id"],
                "symbol": r["symbol"],
                "security_name": r.get("security_name", r["symbol"]),
                "recommendation_date": r.get("recommendation_date", date.today()),
                "signal": r["signal"],
                "confidence": r.get("confidence", 0.5),
                "entry_price_low": r.get("entry_price_low"),
                "entry_price_high": r.get("entry_price_high"),
                "stop_loss": r.get("stop_loss"),
                "target_price": r.get("target_price"),
                "position_size_pct": r.get("position_size_pct", 0.05),
                "max_quantity": r.get("max_quantity", 100),
                "horizon_days": horizon_days,
                "reasons": json.dumps(_json_safe(r.get("reasons", [])), default=str, allow_nan=False),
                "model_version": r.get("model_version", "v1.0"),
                "data_freshness": json.dumps(_json_safe(r.get("data_freshness", {})), default=str, allow_nan=False),
                "logo_url": r.get("logo_url"),
                "expires_at": datetime.utcnow() + timedelta(days=horizon_days),
            })

        # Keep deletion and insertion atomic so a failed refresh preserves prior recommendations.
        current_symbol = None
        try:
            self.session.execute(
                text("DELETE FROM app.recommendations WHERE recommendation_date < :latest_date"),
                {"latest_date": latest_date},
            )
            self.session.execute(
                text("DELETE FROM app.recommendations WHERE UPPER(symbol) = ANY(:symbols)"),
                {"symbols": symbols},
            )
            for params in insert_params:
                current_symbol = params["symbol"]
                self.session.execute(insert_q, params)
            self.session.commit()
        except Exception:
            self.session.rollback()
            logger.exception("Failed saving recommendations%s", f" for {current_symbol}" if current_symbol else "")
            raise
        return len(insert_params)

    def get_active(self, signal_filter: str | None = None) -> list[dict[str, Any]]:
        """Retrieve all currently active recommendations."""
        clause = "WHERE status = 'active'"
        params = {}
        if signal_filter:
            clause += " AND signal = :sig"
            params["sig"] = signal_filter.upper()

        query = text(f"""
            SELECT id, security_id, symbol, security_name, recommendation_date,
                   signal, confidence, entry_price_low, entry_price_high,
                   stop_loss, target_price, position_size_pct, max_quantity,
                   horizon_days, reasons, model_version, status, created_at, logo_url
            FROM app.recommendations
            {clause}
            ORDER BY created_at DESC
        """)
        rows = self.session.execute(query, params).fetchall()
        return [
            {
                "id": r[0],
                "security_id": r[1],
                "symbol": r[2],
                "name": r[3],
                "recommendation_date": str(r[4]),
                "signal": r[5],
                "confidence": float(r[6]) if r[6] else None,
                "entry_price_low": float(r[7]) if r[7] else None,
                "entry_price_high": float(r[8]) if r[8] else None,
                "stop_loss": float(r[9]) if r[9] else None,
                "target_price": float(r[10]) if r[10] else None,
                "position_size_pct": float(r[11]) if r[11] else None,
                "max_quantity": r[12],
                "horizon_days": r[13],
                "reasons": r[14],
                "model_version": r[15],
                "status": r[16],
                "created_at": r[17].isoformat() if r[17] else None,
                "logo_url": r[18],
            }
            for r in rows
        ]

    def update_status(self, rec_id: int, new_status: str) -> bool:
        """Update recommendation status (e.g. executed, cancelled, expired)."""
        query = text("UPDATE app.recommendations SET status = :status WHERE id = :id")
        self.session.execute(query, {"status": new_status, "id": rec_id})
        self.session.commit()
        return True
