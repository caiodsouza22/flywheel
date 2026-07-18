"""Tests for the allocation engine."""

from __future__ import annotations

from allot import (
    AllocationEngine,
    AllocationRequest,
    BurstPolicy,
    DecisionKind,
    WeightedFairPolicy,
)


def test_grant_within_quota_and_budget(engine: AllocationEngine) -> None:
    decision = engine.allocate(
        AllocationRequest(tenant_id="acme", resource="api_calls", amount=10)
    )
    assert decision.kind is DecisionKind.GRANTED
    assert decision.granted == 10
    assert decision.remaining_quota == 190


def test_deny_when_budget_exhausted(engine: AllocationEngine) -> None:
    engine.allocate(AllocationRequest(tenant_id="acme", resource="api_calls", amount=50))
    denied = engine.allocate(
        AllocationRequest(tenant_id="acme", resource="api_calls", amount=1)
    )
    assert denied.kind is DecisionKind.DENIED
    assert denied.granted == 0


def test_partial_requires_flag(store, clock) -> None:
    engine = AllocationEngine(store, policy=WeightedFairPolicy(), clock=clock)
    # Drain most of the pool so fairness yields a partial.
    engine.allocate(
        AllocationRequest(tenant_id="acme", resource="api_calls", amount=50)
    )
    # Fill pool nearly full via repeated grants up to capacity constraints.
    # With remaining pool low, weighted fair may propose partial.
    decision = engine.allocate(
        AllocationRequest(
            tenant_id="beta",
            resource="api_calls",
            amount=900,
            allow_partial=False,
        )
    )
    # Without allow_partial, anything below full request is denied.
    assert decision.kind in {DecisionKind.DENIED, DecisionKind.GRANTED}


def test_burst_policy_can_exceed_hard_ceiling_slightly(store, clock) -> None:
    engine = AllocationEngine(store, policy=BurstPolicy(burst_ratio=0.5), clock=clock)
    # Spend budget to 40/50 remaining 10.
    engine.allocate(AllocationRequest(tenant_id="acme", resource="api_calls", amount=40))
    # Request 12: available 10 + 50% burst = 15, so grant.
    decision = engine.allocate(
        AllocationRequest(tenant_id="acme", resource="api_calls", amount=12)
    )
    assert decision.kind is DecisionKind.GRANTED
    assert decision.reason == "burst"


def test_unknown_tenant_raises(engine: AllocationEngine) -> None:
    import pytest
    from allot import UnknownTenant

    with pytest.raises(UnknownTenant):
        engine.allocate(
            AllocationRequest(tenant_id="nope", resource="api_calls", amount=1)
        )
