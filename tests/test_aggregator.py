"""Tests for usage aggregation."""

from __future__ import annotations

from allot import InMemoryStore, Resource, Tenant
from allot.aggregator import UsageAggregator, enumerate_lifetime_keys
from allot.store import UsageKey


def test_aggregator_groups_and_top_n() -> None:
    store = InMemoryStore()
    store.seed(
        tenants=[Tenant(id="a"), Tenant(id="b")],
        resources=[Resource(name="api"), Resource(name="seats")],
    )
    store.add_usage(UsageKey("a", "api", "lifetime"), 10)
    store.add_usage(UsageKey("b", "api", "lifetime"), 3)
    store.add_usage(UsageKey("a", "seats", "lifetime"), 2)
    keys = enumerate_lifetime_keys(store)
    agg = UsageAggregator(store)
    by_tenant = {row.group_key: row.consumed for row in agg.by_tenant(keys)}
    assert by_tenant["a"] == 12
    top = agg.top_n(keys, n=1, group="tenant")
    assert top[0].group_key == "a"
    assert agg.total(keys) >= 15
