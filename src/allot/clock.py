"""Clock abstractions used by windows and the allocation engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone


class Clock(ABC):
    """Provides the current instant for window evaluation."""

    @abstractmethod
    def now(self) -> datetime:
        """Return an aware UTC datetime."""


class SystemClock(Clock):
    """Wall-clock time in UTC."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class FrozenClock(Clock):
    """Deterministic clock for tests and simulations."""

    def __init__(self, instant: datetime) -> None:
        if instant.tzinfo is None:
            raise ValueError("FrozenClock requires an aware datetime")
        self._instant = instant.astimezone(timezone.utc)

    def now(self) -> datetime:
        return self._instant

    def advance(self, seconds: float) -> None:
        from datetime import timedelta

        if seconds < 0:
            raise ValueError("cannot advance clock backwards; use set()")
        self._instant = self._instant + timedelta(seconds=seconds)

    def set(self, instant: datetime) -> None:
        if instant.tzinfo is None:
            raise ValueError("instant must be timezone-aware")
        self._instant = instant.astimezone(timezone.utc)
