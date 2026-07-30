"""Tests for SqliteStore."""

from __future__ import annotations

from allot import Budget, Quota, Resource, Softness, Tenant
from allot.adapters.sqlite_store import SqliteStore
from allot.store import UsageKey


def test_sqlite_round_trip_registry_and_usage(tmp_path) -> None:
    path = tmp_path / "allot.db"
    store = SqliteStore(path)
    store.seed(
        tenants=[Tenant(id="acme", weight=2, labels={"tier": "pro"})],
        resources=[Resource(name="api", unit="call", capacity=100)],
        quotas=[Quota(tenant_id="acme", resource="api", limit=20, softness=Softness.SOFT)],
        budgets=[
            Budget(
                tenant_id="acme",
                resource="api",
                allowance=5,
                window_seconds=60,
            )
        ],
    )
    assert store.get_tenant("acme").labels["tier"] == "pro"
    assert store.get_resource("api").capacity == 100
    assert store.get_quota("acme", "api").limit == 20
    assert store.get_budget("acme", "api").allowance == 5
    key = UsageKey("acme", "api", "lifetime")
    assert store.add_usage(key, 3) == 3
    assert store.add_usage(key, 2) == 5
    assert store.list_usage_keys()[0].tenant_id == "acme"
    store.reset_usage(key)
    assert store.get_usage(key) == 0
    store.close()

    reopened = SqliteStore(path)
    assert reopened.get_tenant("acme").weight == 2
    reopened.close()


def test_sqlite_list_ordering() -> None:
    store = SqliteStore(":memory:")
    store.put_tenant(Tenant(id="b"))
    store.put_tenant(Tenant(id="a"))
    store.put_resource(Resource(name="z"))
    store.put_resource(Resource(name="m"))
    assert [item.id for item in store.list_tenants()] == ["a", "b"]
    assert [item.name for item in store.list_resources()] == ["m", "z"]
    store.close()
