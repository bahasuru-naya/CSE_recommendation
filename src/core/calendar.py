"""Trading Calendar Dimension: builds and manages core.dim_calendar."""

from __future__ import annotations

from datetime import date, timedelta
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class TradingCalendarBuilder:
    """Populates and maintains core.dim_calendar for date math and holiday checking."""

    def __init__(self, session: Session):
        self.session = session

    def populate(self, start_year: int = 2020, end_year: int = 2030) -> int:
        """Generate dates and insert into core.dim_calendar."""
        logger.info("Generating calendar dimension from %d to %d...", start_year, end_year)

        curr = date(start_year, 1, 1)
        end = date(end_year, 12, 31)

        insert_query = text("""
            INSERT INTO core.dim_calendar (
                calendar_date, year, quarter, month, day_of_week,
                is_trading_day, is_holiday, holiday_name, trading_day_number
            ) VALUES (
                :calendar_date, :year, :quarter, :month, :day_of_week,
                :is_trading_day, :is_holiday, :holiday_name, :trading_day_number
            )
            ON CONFLICT (calendar_date) DO UPDATE SET
                is_trading_day = EXCLUDED.is_trading_day
        """)

        count = 0
        trading_day_num = 1
        curr_year = curr.year

        while curr <= end:
            if curr.year != curr_year:
                curr_year = curr.year
                trading_day_num = 1

            dow = curr.weekday() + 1  # 1=Monday, 7=Sunday
            is_weekend = dow in (6, 7)
            is_trading = not is_weekend

            row = {
                "calendar_date": curr,
                "year": curr.year,
                "quarter": (curr.month - 1) // 3 + 1,
                "month": curr.month,
                "day_of_week": dow,
                "is_trading_day": is_trading,
                "is_holiday": False,
                "holiday_name": None,
                "trading_day_number": trading_day_num if is_trading else None,
            }

            self.session.execute(insert_query, row)
            if is_trading:
                trading_day_num += 1
            count += 1
            curr += timedelta(days=1)

        self.session.commit()
        logger.info("Populated %d calendar records", count)
        return count

    def get_trading_days(self, start: date, end: date) -> list[date]:
        """Fetch all recognized trading days between start and end inclusive."""
        query = text("""
            SELECT calendar_date
            FROM core.dim_calendar
            WHERE calendar_date BETWEEN :start AND :end
              AND is_trading_day = TRUE
            ORDER BY calendar_date
        """)
        rows = self.session.execute(query, {"start": start, "end": end}).fetchall()
        return [r[0] for r in rows]
