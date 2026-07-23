"""Tests for calendar-aligned windows."""

from __future__ import annotations

from datetime import datetime, timezone

from allot.calendar_windows import CalendarUnit, CalendarWindow


def test_day_window() -> None:
    window = CalendarWindow(unit=CalendarUnit.DAY)
    instant = datetime(2024, 3, 10, 15, 30, tzinfo=timezone.utc)
    bounds = window.bounds_at(instant)
    assert bounds.start == datetime(2024, 3, 10, 0, 0, tzinfo=timezone.utc)
    assert bounds.end == datetime(2024, 3, 11, 0, 0, tzinfo=timezone.utc)


def test_hour_and_minute_windows() -> None:
    instant = datetime(2024, 3, 10, 15, 30, 12, tzinfo=timezone.utc)
    hour = CalendarWindow(unit=CalendarUnit.HOUR).bounds_at(instant)
    minute = CalendarWindow(unit=CalendarUnit.MINUTE).bounds_at(instant)
    assert hour.start.minute == 0
    assert minute.start.second == 0
    assert minute.contains(instant)
