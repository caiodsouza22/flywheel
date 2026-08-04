"""Tests for budget forecasting."""

from __future__ import annotations

from datetime import datetime, timezone

from allot import Budget, FrozenClock, InMemoryStore, Resource, Tenant
from allot.budget_forecast import BudgetForecaster
from allot.store import UsageKey
from allot.windows import FixedWindow


def test_forecast_detects_deficit() -> None:
    clock = FrozenClock(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc))
    store = InMemoryStore()
    store.seed(
        tenants=[Tenant(id="acme")],
        resources=[Resource(name="api")],
        budgets=[Budget(tenant_id="acme", resource="api", allowance=100, window_seconds=3600)],
    )
    budget = store.get_budget("acme", "api")
    assert budget is not None
    window = FixedWindow(size_seconds=3600).bounds_at(clock.now())
    store.add_usage(UsageKey("acme", "api", window.start.isoformat()), 80)
    forecaster = BudgetForecaster(store, clock=clock)
    result = forecaster.forecast(budget, demand_per_second=1.0, horizon_seconds=30)
    assert result.survives is False
    assert result.deficit == 10
    assert forecaster.recommend_allowance(demand_per_second=2, window_seconds=60) == 144
