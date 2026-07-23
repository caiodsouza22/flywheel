"""Tests for multi-resource allocation."""

from __future__ import annotations

from allot import AllocationEngine, DecisionKind, InMemoryStore, Quota, Resource, Tenant
from allot.multi_resource import MultiResourceAllocator, MultiResourceRequest, ResourceAmount


def test_multi_resource_partial_abort(clock) -> None:
    store = InMemoryStore()
    store.seed(
        tenants=[Tenant(id="acme")],
        resources=[
            Resource(name="api", capacity=100),
            Resource(name="seats", capacity=2),
        ],
        quotas=[
            Quota(tenant_id="acme", resource="api", limit=100),
            Quota(tenant_id="acme", resource="seats", limit=2),
        ],
    )
    engine = AllocationEngine(store, clock=clock)
    allocator = MultiResourceAllocator(engine)
    decision = allocator.allocate(
        MultiResourceRequest(
            tenant_id="acme",
            items=(
                ResourceAmount("api", 1),
                ResourceAmount("seats", 5),
            ),
        )
    )
    assert decision.kind in {DecisionKind.DENIED, DecisionKind.PARTIAL}
    assert decision.decisions[0].kind is DecisionKind.GRANTED
    assert decision.decisions[1].kind is DecisionKind.DENIED
    assert decision.decisions[1].resource == "seats"
