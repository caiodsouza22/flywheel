"""Tests for the allocation audit log."""

from __future__ import annotations

from datetime import datetime, timezone

from allot import AllocationDecision, AllocationRequest, DecisionKind
from allot.audit import AuditLog


def test_record_and_filter_by_tenant() -> None:
    log = AuditLog()
    request = AllocationRequest(tenant_id="acme", resource="api_calls", amount=3)
    decision = AllocationDecision(
        kind=DecisionKind.GRANTED,
        tenant_id="acme",
        resource="api_calls",
        requested=3,
        granted=3,
    )
    at = datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc)
    log.record(request, decision, at=at)
    assert len(log) == 1
    assert log.for_tenant("acme")[0].decision.granted == 3
    assert log.for_tenant("beta") == []
    assert log.events()[0].to_dict()["at"] == at.isoformat()
