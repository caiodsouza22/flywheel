"""Tests for subscription tiers."""

from __future__ import annotations

from allot import InMemoryStore, Resource
from allot.tiering import compare_tiers, default_saas_tiers


def test_apply_default_tiers() -> None:
    store = InMemoryStore()
    store.put_resource(Resource(name="api_calls", capacity=1_000_000))
    store.put_resource(Resource(name="seats", capacity=1000))
    catalog = default_saas_tiers()
    tenant = catalog.apply(store, "acme", "pro")
    assert tenant.labels["tier"] == "pro"
    assert store.get_quota("acme", "api_calls").limit == 10000
    assert store.get_budget("acme", "api_calls").allowance == 1000
    free = catalog.get("free")
    enterprise = catalog.get("enterprise")
    assert compare_tiers(enterprise, free, "api_calls") == 1
