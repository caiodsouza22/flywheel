"""Tests for circuit breaker."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from allot import FrozenClock
from allot.circuit import CircuitBreaker, CircuitOpen, CircuitState


def test_opens_after_threshold_and_recovers() -> None:
    clock = FrozenClock(datetime(2024, 1, 1, tzinfo=timezone.utc))
    breaker = CircuitBreaker(name="alloc", failure_threshold=2, recovery_seconds=10)
    breaker.set_clock(clock)
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.state is CircuitState.OPEN
    with pytest.raises(CircuitOpen):
        breaker.before_call()
    clock.advance(11)
    assert breaker.state is CircuitState.HALF_OPEN
    breaker.record_success()
    assert breaker.state is CircuitState.CLOSED
