"""Tests for batch allocation."""

from __future__ import annotations

from allot import AllocationEngine, AllocationRequest, DecisionKind
from allot.batch import BatchAllocator


def test_batch_allocates_sequence(engine: AllocationEngine) -> None:
    allocator = BatchAllocator(engine)
    result = allocator.allocate_many(
        [
            AllocationRequest(tenant_id="acme", resource="api_calls", amount=5),
            AllocationRequest(tenant_id="acme", resource="api_calls", amount=5),
        ]
    )
    assert result.granted_total == 10
    assert result.all_granted is True


def test_stop_on_deny(engine: AllocationEngine) -> None:
    allocator = BatchAllocator(engine, stop_on_deny=True)
    result = allocator.allocate_many(
        [
            AllocationRequest(tenant_id="acme", resource="api_calls", amount=50),
            AllocationRequest(tenant_id="acme", resource="api_calls", amount=1),
            AllocationRequest(tenant_id="acme", resource="api_calls", amount=1),
        ]
    )
    assert result.decisions[-1].kind is DecisionKind.DENIED
    assert len(result.decisions) == 2
