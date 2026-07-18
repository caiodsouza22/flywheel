"""Tests for core domain models."""

from __future__ import annotations

import pytest

from allot import AllocationRequest, Budget, DecisionKind, Quota, Resource, Softness, Tenant
from allot.models import AllocationDecision


def test_tenant_rejects_empty_id() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        Tenant(id="")


def test_tenant_rejects_non_positive_weight() -> None:
    with pytest.raises(ValueError, match="positive"):
        Tenant(id="x", weight=0)


def test_resource_rejects_negative_capacity() -> None:
    with pytest.raises(ValueError, match="negative"):
        Resource(name="cpu", capacity=-1)


def test_quota_rejects_negative_limit() -> None:
    with pytest.raises(ValueError, match="negative"):
        Quota(tenant_id="a", resource="r", limit=-1)


def test_budget_rejects_bad_window() -> None:
    with pytest.raises(ValueError, match="positive"):
        Budget(tenant_id="a", resource="r", allowance=10, window_seconds=0)


def test_allocation_request_rejects_non_positive_amount() -> None:
    with pytest.raises(ValueError, match="positive"):
        AllocationRequest(tenant_id="a", resource="r", amount=0)


def test_decision_granted_fully_property() -> None:
    decision = AllocationDecision(
        kind=DecisionKind.GRANTED,
        tenant_id="a",
        resource="r",
        requested=5,
        granted=5,
    )
    assert decision.granted_fully is True
    partial = AllocationDecision(
        kind=DecisionKind.PARTIAL,
        tenant_id="a",
        resource="r",
        requested=5,
        granted=2,
    )
    assert partial.granted_fully is False


def test_softness_values() -> None:
    assert Softness.HARD.value == "hard"
    assert Softness.SOFT.value == "soft"
