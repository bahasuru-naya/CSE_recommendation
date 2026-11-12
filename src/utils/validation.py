"""Validation utilities for CSE data ingestion.

Includes Pydantic models for CSE API response validation, a quarantine
helper for bad records, and price-sanity checks.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Any

from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


# ── Pydantic response models ────────────────────────────────────────────────

class CSEPriceRecord(BaseModel):
    """A single price bar returned by the CSE chart-data endpoints."""

    date: str = Field(..., description="Date string, e.g. '2024-01-15'")
    open: float = Field(..., ge=0)
    high: float = Field(..., ge=0)
    low: float = Field(..., ge=0)
    close: float = Field(..., ge=0)
    volume: float = Field(..., ge=0)

    @field_validator("date")
    @classmethod
    def _validate_date(cls, v: str) -> str:
        """Ensure the date can be parsed."""
        try:
            dt.datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            # Some endpoints use different formats — try ISO as well
            try:
                dt.datetime.fromisoformat(v)
            except ValueError as exc:
                raise ValueError(f"Unparseable date: {v}") from exc
        return v


class CSECompanyInfo(BaseModel):
    """Minimal company-info structure from ``companyInfoSummery``."""

    symbol: str = ""
    company_name: str = Field("", alias="companyName")
    industry: str = ""
    sector: str = ""
    market_cap: float | None = Field(None, alias="marketCap")
    price: float | None = None
    change: float | None = None
    change_percentage: float | None = Field(None, alias="changePercentage")
    volume: float | None = None


class CSEChartDataResponse(BaseModel):
    """Wrapper for the ``chartData`` endpoint response."""

    data: list[dict[str, Any]] = Field(default_factory=list)
    status: str | None = None


class CSECompanyChartDataResponse(BaseModel):
    """Wrapper for the ``companyChartDataByStock`` endpoint response."""

    data: list[dict[str, Any]] = Field(default_factory=list)
    status: str | None = None


# ── Quarantine helper ────────────────────────────────────────────────────────

def quarantine_record(
    session: Session,
    table: str,
    record: dict[str, Any],
    error: str,
) -> None:
    """Insert a bad record into the ``raw.quarantine`` table for later review.

    The quarantine table is expected to have columns:
        id SERIAL, table_name TEXT, record JSONB, error TEXT, created_at TIMESTAMPTZ
    """
    session.execute(
        text(
            """
            INSERT INTO raw.quarantine (table_name, record, error, created_at)
            VALUES (:table_name, :record, :error, NOW())
            """
        ),
        {
            "table_name": table,
            "record": json.dumps(record, default=str),
            "error": str(error),
        },
    )
    session.flush()
    logger.warning("Quarantined record for table=%s: %s", table, error)


# ── Price validation ─────────────────────────────────────────────────────────

def validate_price(row: dict[str, Any], max_change_pct: float = 50.0) -> bool:
    """Run sanity checks on a single OHLCV price row.

    Parameters
    ----------
    row:
        Dictionary with at least ``open``, ``high``, ``low``, ``close``, ``volume``.
    max_change_pct:
        Maximum allowed single-day price change (%). Rows exceeding this
        threshold are flagged as suspicious.

    Returns
    -------
    bool
        ``True`` if the row passes all checks.
    """
    try:
        o = float(row.get("open", 0))
        h = float(row.get("high", 0))
        lo = float(row.get("low", 0))
        c = float(row.get("close", 0))
        v = float(row.get("volume", 0))
    except (TypeError, ValueError):
        logger.debug("Non-numeric OHLCV values: %s", row)
        return False

    # Negative prices are never valid
    if any(p < 0 for p in (o, h, lo, c)):
        logger.debug("Negative price detected: %s", row)
        return False

    # Volume should be non-negative
    if v < 0:
        logger.debug("Negative volume detected: %s", row)
        return False

    # High should be >= Low
    if h < lo:
        logger.debug("High < Low: %s", row)
        return False

    # High should be >= Open and Close; Low should be <= Open and Close
    if h < o or h < c:
        logger.debug("High is less than Open or Close: %s", row)
        return False
    if lo > o or lo > c:
        logger.debug("Low is greater than Open or Close: %s", row)
        return False

    # Extreme intra-day change check
    if o > 0:
        change_pct = abs(c - o) / o * 100
        if change_pct > max_change_pct:
            logger.debug("Extreme change %.1f%% detected: %s", change_pct, row)
            return False

    return True
