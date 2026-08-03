"""Tests for reporting helpers."""

from __future__ import annotations

from allot import (
    AllocationDecision,
    DecisionKind,
    InMemoryStore,
    Resource,
    Tenant,
)
from allot.report import build_system_report, render_text_report
from allot.store import UsageKey


def test_system_report_text() -> None:
    store = InMemoryStore()
    store.seed(tenants=[Tenant(id="acme")], resources=[Resource(name="api")])
    store.add_usage(UsageKey("acme", "api", "lifetime"), 4)
    decisions = [
        AllocationDecision(
            kind=DecisionKind.GRANTED,
            tenant_id="acme",
            resource="api",
            requested=2,
            granted=2,
        ),
        AllocationDecision(
            kind=DecisionKind.DENIED,
            tenant_id="acme",
            resource="api",
            requested=1,
            granted=0,
        ),
    ]
    report = build_system_report(store, decisions)
    text = render_text_report(report)
    assert "acme" in text
    assert report.denial_rate == 0.5
    assert report.to_dict()["usage_total"] == 4
