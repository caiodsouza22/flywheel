"""Tests for validation helpers."""

from __future__ import annotations

import pytest

from allot import AllocationRequest, InMemoryStore, Resource, Tenant
from allot.validation import ValidationError, assert_unique_tenants, validate_request, validate_store_graph


def test_validate_request_ok(store: InMemoryStore) -> None:
    validate_request(
        AllocationRequest(tenant_id="acme", resource="api_calls", amount=1),
        store,
    )


def test_validate_request_unknown_tenant(store: InMemoryStore) -> None:
    with pytest.raises(ValidationError, match="unknown tenant"):
        validate_request(
            AllocationRequest(tenant_id="nope", resource="api_calls", amount=1),
            store,
        )


def test_validate_store_graph_ok(store: InMemoryStore) -> None:
    assert validate_store_graph(store).ok is True


def test_unique_tenants() -> None:
    with pytest.raises(ValidationError):
        assert_unique_tenants([Tenant(id="a"), Tenant(id="a")])
