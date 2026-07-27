"""Tests for retry helper."""

from __future__ import annotations

from allot import AllocationDecision, AllocationRequest, DecisionKind
from allot.retry import RetryPolicy, allocate_with_retry


def test_retry_until_granted() -> None:
    calls = {"n": 0}

    def allocate(request: AllocationRequest) -> AllocationDecision:
        calls["n"] += 1
        kind = DecisionKind.GRANTED if calls["n"] == 3 else DecisionKind.DENIED
        return AllocationDecision(
            kind=kind,
            tenant_id=request.tenant_id,
            resource=request.resource,
            requested=request.amount,
            granted=request.amount if kind is DecisionKind.GRANTED else 0.0,
        )

    decision = allocate_with_retry(
        allocate,
        AllocationRequest(tenant_id="acme", resource="api", amount=1),
        RetryPolicy(max_attempts=5),
    )
    assert decision.kind is DecisionKind.GRANTED
    assert calls["n"] == 3
