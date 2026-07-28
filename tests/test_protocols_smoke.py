"""Smoke tests ensuring protocol-shaped objects remain usable."""

from __future__ import annotations

from allot import AllocationEngine, AllocationRequest
from allot.protocols import SupportsAllocate


def test_engine_matches_supports_allocate(engine: AllocationEngine) -> None:
    allocate: SupportsAllocate = engine
    decision = allocate.allocate(
        AllocationRequest(tenant_id="acme", resource="api_calls", amount=1)
    )
    assert decision.granted == 1
