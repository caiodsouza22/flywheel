"""Evaluation windows for budgets and rate limits."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

from allot.errors import InvalidWindow


class WindowKind(str, Enum):
    FIXED = "fixed"
    SLIDING = "sliding"


@dataclass(frozen=True, slots=True)
class WindowBounds:
    """Half-open interval [start, end) in UTC."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise InvalidWindow("window bounds must be timezone-aware")
        if self.end <= self.start:
            raise InvalidWindow("window end must be after start")

    def contains(self, instant: datetime) -> bool:
        instant = _as_utc(instant)
        return self.start <= instant < self.end

    @property
    def duration_seconds(self) -> float:
        return (self.end - self.start).total_seconds()


class Window(ABC):
    """Computes the active evaluation interval for a given instant."""

    @abstractmethod
    def bounds_at(self, instant: datetime) -> WindowBounds:
        """Return the window that covers ``instant``."""


@dataclass(frozen=True, slots=True)
class FixedWindow(Window):
    """Aligned fixed-size windows (e.g. calendar-like buckets from epoch)."""

    size_seconds: int
    epoch: datetime | None = None

    def __post_init__(self) -> None:
        if self.size_seconds <= 0:
            raise InvalidWindow("fixed window size_seconds must be positive")
        if self.epoch is not None and self.epoch.tzinfo is None:
            raise InvalidWindow("epoch must be timezone-aware")

    def bounds_at(self, instant: datetime) -> WindowBounds:
        instant = _as_utc(instant)
        epoch = self.epoch or datetime(1970, 1, 1, tzinfo=timezone.utc)
        epoch = _as_utc(epoch)
        elapsed = (instant - epoch).total_seconds()
        if elapsed < 0:
            raise InvalidWindow("instant is before window epoch")
        index = int(elapsed // self.size_seconds)
        start = epoch + timedelta(seconds=index * self.size_seconds)
        end = start + timedelta(seconds=self.size_seconds)
        return WindowBounds(start=start, end=end)


@dataclass(frozen=True, slots=True)
class SlidingWindow(Window):
    """Trailing window ending at the evaluation instant."""

    size_seconds: int

    def __post_init__(self) -> None:
        if self.size_seconds <= 0:
            raise InvalidWindow("sliding window size_seconds must be positive")

    def bounds_at(self, instant: datetime) -> WindowBounds:
        instant = _as_utc(instant)
        start = instant - timedelta(seconds=self.size_seconds)
        return WindowBounds(start=start, end=instant)


def _as_utc(instant: datetime) -> datetime:
    if instant.tzinfo is None:
        raise InvalidWindow("instant must be timezone-aware")
    return instant.astimezone(timezone.utc)
