"""Tests for overdraft policy."""

from __future__ import annotations

from allot import AllocationEngine, AllocationRequest, DecisionKind
from allot.overdraft import OverdraftPolicy


def test_overdraft_allows_small_excess(store, clock) -> None:
    engine = AllocationEngine(store, policy=OverdraftPolicy(overdraft=5), clock=clock)
    engine.allocate(AllocationRequest(tenant_id="acme", resource="api_calls", amount=50))
    decision = engine.allocate(
        AllocationRequest(tenant_id="acme", resource="api_calls", amount=4)
    )
    assert decision.kind is DecisionKind.GRANTED
    assert decision.reason == "overdraft"
