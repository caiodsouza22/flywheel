"""Tests for store snapshots."""

from __future__ import annotations

from datetime import datetime, timezone

from allot import FrozenClock, InMemoryStore, Resource, Tenant
from allot.snapshot import restore_snapshot, take_snapshot
from allot.store import UsageKey


def test_snapshot_round_trip() -> None:
    store = InMemoryStore()
    store.seed(tenants=[Tenant(id="acme")], resources=[Resource(name="api", capacity=9)])
    key = UsageKey("acme", "api", "lifetime")
    store.add_usage(key, 3)
    snap = take_snapshot(
        store,
        usage_keys=[key],
        clock=FrozenClock(datetime(2024, 1, 1, tzinfo=timezone.utc)),
    )
    restored = restore_snapshot(snap)
    assert restored.get_tenant("acme").id == "acme"
    assert restored.get_usage(key) == 3
