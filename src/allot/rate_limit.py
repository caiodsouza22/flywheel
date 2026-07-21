"""Token-bucket and leaky-bucket rate limiters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import RLock

from allot.clock import Clock, SystemClock
from allot.errors import AllotError


class RateLimited(AllotError):
    """Raised when a rate limiter rejects a take."""

    def __init__(self, name: str, retry_after_seconds: float) -> None:
        self.name = name
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            f"rate limited: {name}; retry_after_seconds={retry_after_seconds:.3f}"
        )


@dataclass
class TokenBucket:
    """Classic token bucket with continuous refill."""

    name: str
    capacity: float
    refill_per_second: float
    tokens: float | None = None
    _updated_at: datetime | None = None
    _lock: RLock | None = None
    _clock: Clock | None = None

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError("capacity must be positive")
        if self.refill_per_second < 0:
            raise ValueError("refill_per_second cannot be negative")
        if self.tokens is None:
            self.tokens = self.capacity
        if self.tokens < 0 or self.tokens > self.capacity:
            raise ValueError("tokens must be within [0, capacity]")
        self._lock = RLock()
        self._clock = self._clock or SystemClock()
        self._updated_at = self._clock.now()

    def _refill(self, now: datetime) -> None:
        assert self._updated_at is not None and self.tokens is not None
        elapsed = (now - self._updated_at).total_seconds()
        if elapsed <= 0:
            return
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_second)
        self._updated_at = now

    def available(self) -> float:
        assert self._lock is not None and self._clock is not None
        with self._lock:
            self._refill(self._clock.now())
            assert self.tokens is not None
            return self.tokens

    def allow(self, amount: float = 1.0) -> bool:
        if amount <= 0:
            raise ValueError("amount must be positive")
        assert self._lock is not None and self._clock is not None
        with self._lock:
            now = self._clock.now()
            self._refill(now)
            assert self.tokens is not None
            if self.tokens < amount:
                return False
            self.tokens -= amount
            return True

    def take(self, amount: float = 1.0) -> None:
        if not self.allow(amount):
            available = self.available()
            missing = max(0.0, amount - available)
            retry = 0.0 if self.refill_per_second == 0 else missing / self.refill_per_second
            raise RateLimited(self.name, retry)

    def set_clock(self, clock: Clock) -> None:
        assert self._lock is not None
        with self._lock:
            self._clock = clock
            self._updated_at = clock.now()


@dataclass
class LeakyBucket:
    """Leaky bucket that drains at a constant rate and rejects when full."""

    name: str
    capacity: float
    leak_per_second: float
    level: float = 0.0
    _updated_at: datetime | None = None
    _lock: RLock | None = None
    _clock: Clock | None = None

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError("capacity must be positive")
        if self.leak_per_second < 0:
            raise ValueError("leak_per_second cannot be negative")
        if self.level < 0 or self.level > self.capacity:
            raise ValueError("level must be within [0, capacity]")
        self._lock = RLock()
        self._clock = self._clock or SystemClock()
        self._updated_at = self._clock.now()

    def _leak(self, now: datetime) -> None:
        assert self._updated_at is not None
        elapsed = (now - self._updated_at).total_seconds()
        if elapsed <= 0:
            return
        self.level = max(0.0, self.level - elapsed * self.leak_per_second)
        self._updated_at = now

    def offer(self, amount: float = 1.0) -> bool:
        if amount <= 0:
            raise ValueError("amount must be positive")
        assert self._lock is not None and self._clock is not None
        with self._lock:
            now = self._clock.now()
            self._leak(now)
            if self.level + amount > self.capacity:
                return False
            self.level += amount
            return True

    def force_offer(self, amount: float = 1.0) -> None:
        if not self.offer(amount):
            raise RateLimited(self.name, retry_after_seconds=0.0)
