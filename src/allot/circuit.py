"""Circuit breaker to shed load after repeated allocation denials."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import RLock

from allot.clock import Clock, SystemClock
from allot.errors import AllotError


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpen(AllotError):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"circuit open: {name}")


@dataclass
class CircuitBreaker:
    name: str
    failure_threshold: int = 5
    recovery_seconds: float = 30.0
    _failures: int = 0
    _state: CircuitState = CircuitState.CLOSED
    _opened_at: datetime | None = None
    _lock: RLock = field(default_factory=RLock)
    _clock: Clock = field(default_factory=SystemClock)

    def __post_init__(self) -> None:
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if self.recovery_seconds <= 0:
            raise ValueError("recovery_seconds must be positive")

    def set_clock(self, clock: Clock) -> None:
        self._clock = clock

    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._maybe_half_open_locked(self._clock.now())
            return self._state

    def before_call(self) -> None:
        with self._lock:
            now = self._clock.now()
            self._maybe_half_open_locked(now)
            if self._state is CircuitState.OPEN:
                raise CircuitOpen(self.name)

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._state = CircuitState.CLOSED
            self._opened_at = None

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = self._clock.now()

    def _maybe_half_open_locked(self, now: datetime) -> None:
        if self._state is CircuitState.OPEN and self._opened_at is not None:
            if now >= self._opened_at + timedelta(seconds=self.recovery_seconds):
                self._state = CircuitState.HALF_OPEN
