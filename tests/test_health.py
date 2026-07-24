"""Tests for health checks."""

from __future__ import annotations

from allot import InMemoryStore, Resource, Tenant
from allot.health import HealthCheck, run_health


def test_health_report() -> None:
    store = InMemoryStore()
    store.seed(tenants=[Tenant(id="a")], resources=[Resource(name="r")])
    report = run_health(store, extra=[lambda: HealthCheck(name="custom", ok=True)])
    assert report.healthy is True
    assert report.checks[0].name == "store"
