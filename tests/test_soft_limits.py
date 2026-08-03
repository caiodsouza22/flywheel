"""Tests for soft-limit breach tracking."""

from __future__ import annotations

from allot import (
    AllocationDecision,
    AllocationRequest,
    DecisionKind,
    InMemoryStore,
    Quota,
    Resource,
    Softness,
    Tenant,
)
from allot.soft_limits import SoftLimitTracker


def test_soft_breach_recorded() -> None:
    store = InMemoryStore()
    store.seed(
        tenants=[Tenant(id="acme")],
        resources=[Resource(name="api")],
        quotas=[Quota(tenant_id="acme", resource="api", limit=5, softness=Softness.SOFT)],
    )
    tracker = SoftLimitTracker(store)
    request = AllocationRequest(tenant_id="acme", resource="api", amount=3)
    decision = AllocationDecision(
        kind=DecisionKind.GRANTED,
        tenant_id="acme",
        resource="api",
        requested=3,
        granted=3,
    )
    breach = tracker.observe(request, decision, remaining_before=2)
    assert breach is not None
    assert tracker.count() == 1
    assert tracker.breaches(tenant_id="acme")[0].remaining_before == 2
