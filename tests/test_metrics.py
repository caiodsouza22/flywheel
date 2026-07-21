"""Tests for metrics registry."""

from __future__ import annotations

from allot import AllocationDecision, DecisionKind, MetricsRegistry


def test_observe_decision_and_prometheus_render() -> None:
    metrics = MetricsRegistry()
    metrics.observe_decision(
        AllocationDecision(
            kind=DecisionKind.GRANTED,
            tenant_id="acme",
            resource="api",
            requested=4,
            granted=4,
        )
    )
    metrics.observe_decision(
        AllocationDecision(
            kind=DecisionKind.DENIED,
            tenant_id="acme",
            resource="api",
            requested=1,
            granted=0,
            reason="insufficient_capacity",
        )
    )
    snap = metrics.snapshot()
    assert any(row["name"] == "allot_allocations_total" for row in snap)
    text = metrics.render_prometheus()
    assert "allot_denials_total" in text
    assert 'tenant="acme"' in text
