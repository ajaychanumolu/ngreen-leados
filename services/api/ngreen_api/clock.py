"""Dates used for follow-ups. Calling hours and overdue tasks share India time."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

INDIA = ZoneInfo("Asia/Kolkata")


def india_today() -> date:
    return datetime.now(INDIA).date()
