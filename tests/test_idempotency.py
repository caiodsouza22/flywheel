"""Tests for idempotency store."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from allot import AllocationDecision, AllocationRequest, DecisionKind, FrozenClock
from allot.idempotency import IdempotencyConflict, IdempotencyStore


def test_remember_and_replay() -> None:
    clock = FrozenClock(datetime(2024, 1, 1, tzinfo=timezone.utc))
    store = IdempotencyStore(ttl_seconds=60)
    store.set_clock(clock)
    request = AllocationRequest(tenant_id="acme", resource="api", amount=2)
    decision = AllocationDecision(
        kind=DecisionKind.GRANTED,
        tenant_id="acme",
        resource="api",
        requested=2,
        granted=2,
    )
    store.remember("k1", request, decision)
    assert store.replay_or_none("k1", request) == decision


def test_conflict_on_fingerprint_mismatch() -> None:
    store = IdempotencyStore(ttl_seconds=60)
    request = AllocationRequest(tenant_id="acme", resource="api", amount=2)
    decision = AllocationDecision(
        kind=DecisionKind.GRANTED,
        tenant_id="acme",
        resource="api",
        requested=2,
        granted=2,
    )
    store.remember("k1", request, decision)
    other = AllocationRequest(tenant_id="acme", resource="api", amount=3)
    with pytest.raises(IdempotencyConflict):
        store.remember("k1", other, decision)


def test_ttl_expiry() -> None:
    clock = FrozenClock(datetime(2024, 1, 1, tzinfo=timezone.utc))
    store = IdempotencyStore(ttl_seconds=10)
    store.set_clock(clock)
    request = AllocationRequest(tenant_id="acme", resource="api", amount=1)
    decision = AllocationDecision(
        kind=DecisionKind.GRANTED,
        tenant_id="acme",
        resource="api",
        requested=1,
        granted=1,
    )
    store.remember("k1", request, decision)
    clock.advance(11)
    assert store.get("k1") is None
