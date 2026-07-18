"""Tests for the in-memory store."""

from __future__ import annotations

import pytest

from allot import InMemoryStore, Quota, Resource, Tenant, UnknownResource, UnknownTenant
from allot.store import UsageKey


def test_put_and_get_tenant() -> None:
    store = InMemoryStore()
    store.put_tenant(Tenant(id="acme"))
    assert store.get_tenant("acme").id == "acme"


def test_unknown_tenant() -> None:
    store = InMemoryStore()
    with pytest.raises(UnknownTenant):
        store.get_tenant("missing")


def test_quota_requires_registered_tenant_and_resource() -> None:
    store = InMemoryStore()
    store.put_tenant(Tenant(id="acme"))
    with pytest.raises(UnknownResource):
        store.put_quota(Quota(tenant_id="acme", resource="api", limit=10))


def test_usage_add_and_reset() -> None:
    store = InMemoryStore()
    key = UsageKey("acme", "api", "lifetime")
    assert store.get_usage(key) == 0.0
    assert store.add_usage(key, 3.5) == 3.5
    assert store.add_usage(key, 1.5) == 5.0
    store.reset_usage(key)
    assert store.get_usage(key) == 0.0


def test_seed_registers_graph() -> None:
    store = InMemoryStore()
    store.seed(
        tenants=[Tenant(id="a")],
        resources=[Resource(name="r", capacity=9)],
        quotas=[Quota(tenant_id="a", resource="r", limit=4)],
    )
    assert store.list_tenants()[0].id == "a"
    assert store.get_resource("r").capacity == 9
    assert store.get_quota("a", "r") is not None
