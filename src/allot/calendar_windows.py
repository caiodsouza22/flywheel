"""Calendar-aligned evaluation windows (day/hour/minute boundaries in UTC)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

from allot.errors import InvalidWindow
from allot.windows import Window, WindowBounds


class CalendarUnit(str, Enum):
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


@dataclass(frozen=True, slots=True)
class CalendarWindow(Window):
    """Windows aligned to UTC calendar boundaries."""

    unit: CalendarUnit

    def bounds_at(self, instant: datetime) -> WindowBounds:
        if instant.tzinfo is None:
            raise InvalidWindow("instant must be timezone-aware")
        instant = instant.astimezone(timezone.utc)
        if self.unit is CalendarUnit.MINUTE:
            start = instant.replace(second=0, microsecond=0)
            end = start + timedelta(minutes=1)
        elif self.unit is CalendarUnit.HOUR:
            start = instant.replace(minute=0, second=0, microsecond=0)
            end = start + timedelta(hours=1)
        elif self.unit is CalendarUnit.DAY:
            start = instant.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        else:
            raise InvalidWindow(f"unsupported calendar unit: {self.unit}")
        return WindowBounds(start=start, end=end)
