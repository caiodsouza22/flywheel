"""TTL cache for expensive registry lookups."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import RLock
from typing import Callable, Generic, Hashable, TypeVar

from allot.clock import Clock, SystemClock

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


@dataclass
class _Entry(Generic[V]):
    value: V
    expires_at: datetime


@dataclass
class TtlCache(Generic[K, V]):
    ttl_seconds: float
    max_size: int = 1024
    _data: dict[K, _Entry[V]] = field(default_factory=dict)
    _lock: RLock = field(default_factory=RLock)
    _clock: Clock = field(default_factory=SystemClock)
    hits: int = 0
    misses: int = 0

    def __post_init__(self) -> None:
        if self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if self.max_size < 1:
            raise ValueError("max_size must be >= 1")

    def set_clock(self, clock: Clock) -> None:
        self._clock = clock

    def get(self, key: K) -> V | None:
        now = self._clock.now()
        with self._lock:
            entry = self._data.get(key)
            if entry is None or now >= entry.expires_at:
                if entry is not None:
                    del self._data[key]
                self.misses += 1
                return None
            self.hits += 1
            return entry.value

    def set(self, key: K, value: V) -> None:
        now = self._clock.now()
        with self._lock:
            if len(self._data) >= self.max_size and key not in self._data:
                # Drop an arbitrary expired or oldest-ish item.
                self._evict_one_locked(now)
            self._data[key] = _Entry(
                value=value,
                expires_at=now + timedelta(seconds=self.ttl_seconds),
            )

    def get_or_set(self, key: K, factory: Callable[[], V]) -> V:
        cached = self.get(key)
        if cached is not None:
            return cached
        value = factory()
        self.set(key, value)
        return value

    def invalidate(self, key: K) -> None:
        with self._lock:
            self._data.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {
                "hits": self.hits,
                "misses": self.misses,
                "size": len(self._data),
            }

    def _evict_one_locked(self, now: datetime) -> None:
        for key, entry in list(self._data.items()):
            if now >= entry.expires_at:
                del self._data[key]
                return
        # Fallback: pop first key.
        if self._data:
            self._data.pop(next(iter(self._data)))
