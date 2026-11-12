"""Time-related utilities for CSE market hours (Asia/Colombo, UTC+5:30)."""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

# ── Constants ─────────────────────────────────────────────────────────────────
COLOMBO_TZ = ZoneInfo("Asia/Colombo")
_MARKET_OPEN = dt.time(9, 30)
_MARKET_CLOSE = dt.time(14, 30)
_WEEKDAYS = range(0, 5)  # Mon-Fri


# ── Helpers ───────────────────────────────────────────────────────────────────
def utc_now() -> dt.datetime:
    """Return the current UTC time as an aware datetime."""
    return dt.datetime.now(dt.timezone.utc)


def colombo_now() -> dt.datetime:
    """Return the current time in Asia/Colombo."""
    return dt.datetime.now(COLOMBO_TZ)


def trading_date(when: dt.datetime | None = None) -> dt.date:
    """Determine the effective CSE trading date for a given instant.

    If *when* is before market open (09:30 Colombo) or on a weekend the
    function returns the **previous business day**.  Otherwise it returns
    ``when.date()``.
    """
    if when is None:
        when = colombo_now()
    elif when.tzinfo is None:
        when = when.replace(tzinfo=COLOMBO_TZ)
    else:
        when = when.astimezone(COLOMBO_TZ)

    d = when.date()

    # Before market open → previous business day
    if when.time() < _MARKET_OPEN:
        d -= dt.timedelta(days=1)

    # Walk backwards past weekends
    while d.weekday() not in _WEEKDAYS:
        d -= dt.timedelta(days=1)

    return d


def is_market_hours(when: dt.datetime | None = None) -> bool:
    """Return ``True`` if *when* falls within CSE trading hours.

    CSE trades Monday-Friday 09:30-14:30 Sri Lanka time.
    """
    if when is None:
        when = colombo_now()
    elif when.tzinfo is None:
        when = when.replace(tzinfo=COLOMBO_TZ)
    else:
        when = when.astimezone(COLOMBO_TZ)

    if when.weekday() not in _WEEKDAYS:
        return False
    return _MARKET_OPEN <= when.time() <= _MARKET_CLOSE


def next_market_open(when: dt.datetime | None = None) -> dt.datetime:
    """Return the next market-open instant (09:30 Colombo).

    If the market is currently open, the *following* day's open is returned.
    """
    if when is None:
        when = colombo_now()
    elif when.tzinfo is None:
        when = when.replace(tzinfo=COLOMBO_TZ)
    else:
        when = when.astimezone(COLOMBO_TZ)

    candidate = when.replace(hour=9, minute=30, second=0, microsecond=0)

    # If we're already past today's open, start from tomorrow
    if when >= candidate:
        candidate += dt.timedelta(days=1)

    # Skip weekends
    while candidate.weekday() not in _WEEKDAYS:
        candidate += dt.timedelta(days=1)

    return candidate


def business_days_between(start: dt.date, end: dt.date) -> int:
    """Count the number of weekday (Mon-Fri) days in ``[start, end)``.

    CSE-specific holidays are **not** accounted for — this is a simple
    weekday count.
    """
    if end <= start:
        return 0

    count = 0
    current = start
    while current < end:
        if current.weekday() in _WEEKDAYS:
            count += 1
        current += dt.timedelta(days=1)
    return count
