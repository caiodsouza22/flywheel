"""Tests for composite policies."""

from __future__ import annotations

from allot import Softness, StrictPolicy, Tenant
from allot.composite_policy import FirstAllowPolicy, MinGrantPolicy
from allot.policies import BurstPolicy, PolicyContext, WeightedFairPolicy


def _ctx(requested: float = 10, remaining_pool: float | None = 5) -> PolicyContext:
    return PolicyContext(
        tenant=Tenant(id="acme", weight=1),
        requested=requested,
        remaining_quota=None,
        remaining_budget=None,
        remaining_pool=remaining_pool,
        softness=Softness.HARD,
    )


def test_first_allow_returns_burst() -> None:
    policy = FirstAllowPolicy(policies=(StrictPolicy(), BurstPolicy(burst_ratio=1.0)))
    result = policy.decide(_ctx(requested=10, remaining_pool=5))
    assert result.granted == 10


def test_min_grant() -> None:
    policy = MinGrantPolicy(policies=(WeightedFairPolicy(), StrictPolicy()))
    result = policy.decide(_ctx(requested=10, remaining_pool=5))
    assert result.granted == 0.0 or result.granted <= 5
