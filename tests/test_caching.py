"""Tests for TTL cache."""

from __future__ import annotations

from datetime import datetime, timezone

from allot import FrozenClock
from allot.caching import TtlCache


def test_cache_hit_miss_and_expiry() -> None:
    clock = FrozenClock(datetime(2024, 1, 1, tzinfo=timezone.utc))
    cache: TtlCache[str, int] = TtlCache(ttl_seconds=10, max_size=2)
    cache.set_clock(clock)
    assert cache.get("a") is None
    cache.set("a", 1)
    assert cache.get("a") == 1
    assert cache.get_or_set("b", lambda: 2) == 2
    clock.advance(11)
    assert cache.get("a") is None
    stats = cache.stats()
    assert stats["misses"] >= 2
    assert stats["hits"] >= 1
