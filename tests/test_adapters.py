"""Tests for store adapters."""

from __future__ import annotations

import pytest

from allot import InMemoryStore, Resource, Tenant
from allot.adapters import DictStoreAdapter, ReadOnlyStore
from allot.adapters.readonly import ReadOnlyViolation


def test_dict_store_adapter() -> None:
    store = DictStoreAdapter.from_mapping(
        {
            "version": 1,
            "tenants": [{"id": "acme"}],
            "resources": [{"name": "api", "capacity": 10}],
            "quotas": [],
            "budgets": [],
        }
    )
    assert store.get_tenant("acme").id == "acme"


def test_readonly_blocks_mutation() -> None:
    store = InMemoryStore()
    store.seed(tenants=[Tenant(id="a")], resources=[Resource(name="r")])
    ro = ReadOnlyStore(store)
    assert ro.get_tenant("a").id == "a"
    with pytest.raises(ReadOnlyViolation):
        ro.put_tenant(Tenant(id="b"))
