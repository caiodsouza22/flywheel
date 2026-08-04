"""Tests for tenant label index."""

from __future__ import annotations

from allot import InMemoryStore, Tenant
from allot.tenant_index import TenantIndex


def test_index_finds_by_tier_and_counts() -> None:
    store = InMemoryStore()
    store.put_tenant(Tenant(id="a", labels={"tier": "pro", "region": "us"}))
    store.put_tenant(Tenant(id="b", labels={"tier": "free", "region": "us"}))
    store.put_tenant(Tenant(id="c", labels={"tier": "pro", "region": "eu"}))
    index = TenantIndex()
    index.rebuild(store)
    assert [tenant.id for tenant in index.find_by_tier("pro")] == ["a", "c"]
    assert index.counts_by_label("region") == {"eu": 1, "us": 2}
    index.upsert(Tenant(id="a", labels={"tier": "enterprise", "region": "us"}))
    assert [tenant.id for tenant in index.find_by_tier("enterprise")] == ["a"]
