"""Tests for weighted fair queue."""

from __future__ import annotations

from allot import AllocationRequest, FairQueue, Tenant


def test_higher_weight_is_served_preferentially_under_load() -> None:
    queue = FairQueue()
    heavy = Tenant(id="heavy", weight=4.0)
    light = Tenant(id="light", weight=1.0)
    queue.enqueue(AllocationRequest(tenant_id="light", resource="api", amount=10), light)
    queue.enqueue(AllocationRequest(tenant_id="heavy", resource="api", amount=10), heavy)
    # Same amount: higher weight gets earlier virtual finish.
    first = queue.dequeue()
    assert first.tenant_id == "heavy"
    second = queue.dequeue()
    assert second.tenant_id == "light"


def test_drain_and_empty() -> None:
    queue = FairQueue()
    tenant = Tenant(id="a")
    queue.enqueue(AllocationRequest(tenant_id="a", resource="r", amount=1), tenant)
    queue.enqueue(AllocationRequest(tenant_id="a", resource="r", amount=1), tenant)
    assert len(queue.drain(limit=1)) == 1
    assert len(queue) == 1
    assert queue.peek() is not None
    queue.drain()
    assert queue.peek() is None
