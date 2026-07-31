"""Tests for limit schedules."""

from __future__ import annotations

from datetime import datetime, timezone

from allot.clock import FrozenClock
from allot.schedules import (
    LimitSchedule,
    ScheduleBook,
    TimeWindowRule,
    Weekday,
    business_hours_schedule,
    combine_schedules,
    weekend_boost_schedule,
)


def test_business_hours_and_weekend() -> None:
    weekday_peak = datetime(2024, 3, 11, 10, 0, tzinfo=timezone.utc)  # Monday
    weekend = datetime(2024, 3, 16, 10, 0, tzinfo=timezone.utc)  # Saturday
    schedule = business_hours_schedule(peak_multiplier=1.0, offpeak_multiplier=2.0)
    assert schedule.multiplier_at(weekday_peak) == 1.0
    boost = weekend_boost_schedule(3.0)
    assert boost.multiplier_at(weekend) == 3.0
    assert combine_schedules([schedule, boost], weekend) == 6.0


def test_schedule_book_effective_limit() -> None:
    clock = FrozenClock(datetime(2024, 3, 11, 10, 0, tzinfo=timezone.utc))
    book = ScheduleBook(clock=clock)
    book.put(
        "api",
        LimitSchedule(
            rules=[
                TimeWindowRule(
                    name="peak",
                    start_hour=9,
                    end_hour=17,
                    multiplier=0.5,
                    weekdays=frozenset({Weekday.MONDAY}),
                )
            ],
            default_multiplier=1.0,
        ),
    )
    assert book.effective_limit("api", 100) == 50
