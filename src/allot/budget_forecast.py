"""Forecast whether budgets survive projected demand."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from allot.clock import Clock, SystemClock
from allot.models import Budget
from allot.quota_math import project_burn
from allot.sliding_budget import SlidingBudgetAccount
from allot.store import Store, UsageKey
from allot.windows import FixedWindow


@dataclass(frozen=True, slots=True)
class ForecastResult:
    tenant_id: str
    resource: str
    remaining: float
    projected_demand: float
    survives: bool
    deficit: float
    seconds_to_exhaustion: float | None


@dataclass
class BudgetForecaster:
    store: Store
    clock: Clock | None = None

    def __post_init__(self) -> None:
        self.clock = self.clock or SystemClock()

    def remaining_fixed_budget(self, budget: Budget, now: datetime | None = None) -> float:
        now = now or self.clock.now()
        window = FixedWindow(size_seconds=budget.window_seconds)
        bounds = window.bounds_at(now)
        used = self.store.get_usage(
            UsageKey(budget.tenant_id, budget.resource, bounds.start.isoformat())
        )
        return max(0.0, budget.allowance - used)

    def forecast(
        self,
        budget: Budget,
        *,
        demand_per_second: float,
        horizon_seconds: float,
        now: datetime | None = None,
    ) -> ForecastResult:
        if demand_per_second < 0 or horizon_seconds < 0:
            raise ValueError("demand and horizon cannot be negative")
        now = now or self.clock.now()
        remaining = self.remaining_fixed_budget(budget, now)
        projected = demand_per_second * horizon_seconds
        burn = project_burn(remaining=remaining, burn_per_second=demand_per_second)
        deficit = max(0.0, projected - remaining)
        return ForecastResult(
            tenant_id=budget.tenant_id,
            resource=budget.resource,
            remaining=remaining,
            projected_demand=projected,
            survives=deficit == 0,
            deficit=deficit,
            seconds_to_exhaustion=burn.seconds_to_exhaustion,
        )

    def forecast_sliding(
        self,
        account: SlidingBudgetAccount,
        *,
        demand_per_second: float,
        horizon_seconds: float,
        now: datetime | None = None,
    ) -> ForecastResult:
        now = now or self.clock.now()
        remaining = account.remaining(now)
        projected = demand_per_second * horizon_seconds
        burn = project_burn(remaining=remaining, burn_per_second=demand_per_second)
        deficit = max(0.0, projected - remaining)
        return ForecastResult(
            tenant_id=account.tenant_id,
            resource=account.resource,
            remaining=remaining,
            projected_demand=projected,
            survives=deficit == 0,
            deficit=deficit,
            seconds_to_exhaustion=burn.seconds_to_exhaustion,
        )

    def recommend_allowance(
        self,
        *,
        demand_per_second: float,
        window_seconds: int,
        safety_factor: float = 1.2,
    ) -> float:
        if demand_per_second < 0 or window_seconds <= 0 or safety_factor < 1:
            raise ValueError("invalid recommendation inputs")
        return demand_per_second * window_seconds * safety_factor

    def exhaustion_at(
        self,
        budget: Budget,
        *,
        demand_per_second: float,
        now: datetime | None = None,
    ) -> datetime | None:
        result = self.forecast(
            budget,
            demand_per_second=demand_per_second,
            horizon_seconds=budget.window_seconds,
            now=now,
        )
        if result.seconds_to_exhaustion is None:
            return None
        base = now or self.clock.now()
        return base + timedelta(seconds=result.seconds_to_exhaustion)
