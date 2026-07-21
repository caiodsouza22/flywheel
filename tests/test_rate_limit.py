"""Tests for token and leaky buckets."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from allot.clock import FrozenClock
from allot.rate_limit import LeakyBucket, RateLimited, TokenBucket


def test_token_bucket_refills_and_takes() -> None:
    clock = FrozenClock(datetime(2024, 1, 1, tzinfo=timezone.utc))
    bucket = TokenBucket(name="api", capacity=10, refill_per_second=1, _clock=clock)
    assert bucket.allow(10) is True
    assert bucket.allow(1) is False
    clock.advance(5)
    assert bucket.available() == pytest.approx(5)
    bucket.take(5)
    with pytest.raises(RateLimited):
        bucket.take(1)


def test_leaky_bucket_rejects_when_full() -> None:
    clock = FrozenClock(datetime(2024, 1, 1, tzinfo=timezone.utc))
    bucket = LeakyBucket(name="q", capacity=5, leak_per_second=1, _clock=clock)
    assert bucket.offer(5) is True
    assert bucket.offer(1) is False
    clock.advance(2)
    assert bucket.offer(2) is True
