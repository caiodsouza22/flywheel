"""Tests for quota math helpers."""

from __future__ import annotations

from allot.quota_math import (
    ema,
    fair_share,
    project_burn,
    replenish_amount,
    utilization_band,
)


def test_burn_and_replenish() -> None:
    projection = project_burn(remaining=100, burn_per_second=10)
    assert projection.seconds_to_exhaustion == 10
    assert replenish_amount(
        capacity=10,
        current=2,
        refill_per_second=1,
        elapsed_seconds=100,
    ) == 10


def test_fair_share_and_bands() -> None:
    shares = fair_share(100, {"a": 1, "b": 3})
    assert shares["a"] == 25
    assert shares["b"] == 75
    assert utilization_band(0.2) == "low"
    assert utilization_band(0.97) == "critical"
    assert ema(10, 20, alpha=0.5) == 15
