"""Time-of-day and weekday schedules that scale effective limits."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Iterable

from allot.clock import Clock, SystemClock
from allot.errors import AllotError


class ScheduleError(AllotError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class Weekday(int, Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


@dataclass(frozen=True, slots=True)
class TimeWindowRule:
    name: str
    start_hour: int
    end_hour: int
    multiplier: float
    weekdays: frozenset[Weekday] | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.start_hour <= 24:
            raise ScheduleError("start_hour must be within 0..24")
        if not 0 <= self.end_hour <= 24:
            raise ScheduleError("end_hour must be within 0..24")
        if self.start_hour == self.end_hour:
            raise ScheduleError("start_hour and end_hour cannot be equal")
        if self.multiplier < 0:
            raise ScheduleError("multiplier cannot be negative")

    def matches(self, instant: datetime) -> bool:
        if instant.tzinfo is None:
            raise ScheduleError("instant must be timezone-aware")
        weekday = Weekday(instant.weekday())
        if self.weekdays is not None and weekday not in self.weekdays:
            return False
        hour = instant.hour + instant.minute / 60.0 + instant.second / 3600.0
        if self.start_hour < self.end_hour:
            return self.start_hour <= hour < self.end_hour
        return hour >= self.start_hour or hour < self.end_hour


@dataclass
class LimitSchedule:
    rules: list[TimeWindowRule]
    default_multiplier: float = 1.0

    def __post_init__(self) -> None:
        if self.default_multiplier < 0:
            raise ScheduleError("default_multiplier cannot be negative")

    def multiplier_at(self, instant: datetime) -> float:
        for rule in self.rules:
            if rule.matches(instant):
                return rule.multiplier
        return self.default_multiplier

    def scale(self, base_limit: float, instant: datetime) -> float:
        if base_limit < 0:
            raise ValueError("base_limit cannot be negative")
        return base_limit * self.multiplier_at(instant)


class ScheduleBook:
    def __init__(self, *, clock: Clock | None = None) -> None:
        self._clock = clock or SystemClock()
        self._schedules: dict[str, LimitSchedule] = {}

    def put(self, name: str, schedule: LimitSchedule) -> None:
        if not name:
            raise ScheduleError("schedule name must be non-empty")
        self._schedules[name] = schedule

    def get(self, name: str) -> LimitSchedule:
        try:
            return self._schedules[name]
        except KeyError as exc:
            raise ScheduleError(f"unknown schedule: {name}") from exc

    def effective_limit(self, name: str, base_limit: float) -> float:
        schedule = self.get(name)
        return schedule.scale(base_limit, self._clock.now())

    def names(self) -> list[str]:
        return sorted(self._schedules)

    def bind_many(self, mapping: dict[str, LimitSchedule]) -> None:
        for name, schedule in mapping.items():
            self.put(name, schedule)


def business_hours_schedule(
    *,
    peak_multiplier: float = 1.0,
    offpeak_multiplier: float = 1.5,
) -> LimitSchedule:
    weekdays = frozenset(
        {
            Weekday.MONDAY,
            Weekday.TUESDAY,
            Weekday.WEDNESDAY,
            Weekday.THURSDAY,
            Weekday.FRIDAY,
        }
    )
    return LimitSchedule(
        rules=[
            TimeWindowRule(
                name="business_hours",
                start_hour=9,
                end_hour=17,
                multiplier=peak_multiplier,
                weekdays=weekdays,
            ),
            TimeWindowRule(
                name="weekday_offpeak",
                start_hour=0,
                end_hour=24,
                multiplier=offpeak_multiplier,
                weekdays=weekdays,
            ),
        ],
        default_multiplier=offpeak_multiplier,
    )


def weekend_boost_schedule(multiplier: float = 2.0) -> LimitSchedule:
    weekend = frozenset({Weekday.SATURDAY, Weekday.SUNDAY})
    return LimitSchedule(
        rules=[
            TimeWindowRule(
                name="weekend",
                start_hour=0,
                end_hour=24,
                multiplier=multiplier,
                weekdays=weekend,
            )
        ],
        default_multiplier=1.0,
    )


def combine_schedules(schedules: Iterable[LimitSchedule], instant: datetime) -> float:
    product = 1.0
    for schedule in schedules:
        product *= schedule.multiplier_at(instant)
    return product
