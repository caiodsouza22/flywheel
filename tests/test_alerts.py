"""Tests for alert hub."""

from __future__ import annotations

from allot import AllocationDecision, DecisionKind, InMemoryStore, Resource, Tenant
from allot.alerts import AlertHub, AlertSeverity, CollectingHandler, ThresholdRule
from allot.store import UsageKey


def test_usage_and_denial_alerts() -> None:
    store = InMemoryStore()
    store.seed(tenants=[Tenant(id="acme")], resources=[Resource(name="api")])
    store.add_usage(UsageKey("acme", "api", "lifetime"), 8)
    hub = AlertHub()
    handler = CollectingHandler()
    hub.add_handler(handler)
    alerts = hub.check_usage_ratio(
        store,
        tenant_id="acme",
        resource="api",
        limit=10,
        rules=[
            ThresholdRule(name="warn", ratio=0.5, severity=AlertSeverity.WARNING),
            ThresholdRule(name="crit", ratio=0.8, severity=AlertSeverity.CRITICAL),
        ],
    )
    assert len(alerts) == 2
    denial = hub.check_denial_rate(
        [
            AllocationDecision(
                kind=DecisionKind.DENIED,
                tenant_id="acme",
                resource="api",
                requested=1,
                granted=0,
            ),
            AllocationDecision(
                kind=DecisionKind.GRANTED,
                tenant_id="acme",
                resource="api",
                requested=1,
                granted=1,
            ),
        ],
        threshold=0.4,
    )
    assert denial is not None
    assert len(handler.alerts) >= 3
