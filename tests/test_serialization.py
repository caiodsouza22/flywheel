"""Tests for JSON serialization helpers."""

from __future__ import annotations

from allot import (
    AllocationDecision,
    AllocationRequest,
    Budget,
    DecisionKind,
    Quota,
    Resource,
    Softness,
    Tenant,
)
from allot import serialization as ser


def test_round_trip_tenant_resource_quota_budget() -> None:
    tenant = Tenant(id="acme", weight=2.0, labels={"tier": "gold"})
    resource = Resource(name="api", unit="call", capacity=100)
    quota = Quota(tenant_id="acme", resource="api", limit=10, softness=Softness.SOFT)
    budget = Budget(
        tenant_id="acme",
        resource="api",
        allowance=5,
        window_seconds=60,
    )
    assert ser.tenant_from_dict(ser.tenant_to_dict(tenant)) == tenant
    assert ser.resource_from_dict(ser.resource_to_dict(resource)) == resource
    assert ser.quota_from_dict(ser.quota_to_dict(quota)) == quota
    assert ser.budget_from_dict(ser.budget_to_dict(budget)) == budget


def test_decision_dumps_sorted_json() -> None:
    decision = AllocationDecision(
        kind=DecisionKind.GRANTED,
        tenant_id="acme",
        resource="api",
        requested=3,
        granted=3,
        remaining_quota=7,
        reason=None,
    )
    text = ser.dumps(decision)
    assert '"kind": "granted"' in text
    loaded = ser.decision_from_dict(ser.decision_to_dict(decision))
    assert loaded.granted_fully is True


def test_request_round_trip() -> None:
    request = AllocationRequest(
        tenant_id="acme",
        resource="api",
        amount=2,
        allow_partial=True,
        metadata={"trace": "1"},
    )
    assert ser.request_from_dict(ser.request_to_dict(request)) == request
