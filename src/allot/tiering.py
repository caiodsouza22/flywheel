"""Subscription tiers that expand into concrete quotas and budgets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from allot.errors import AllotError
from allot.models import Budget, Quota, Softness, Tenant
from allot.store import Store


class TierError(AllotError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class TierQuotaSpec:
    resource: str
    limit: float
    softness: Softness = Softness.HARD


@dataclass(frozen=True, slots=True)
class TierBudgetSpec:
    resource: str
    allowance: float
    window_seconds: int
    softness: Softness = Softness.HARD


@dataclass(frozen=True, slots=True)
class Tier:
    name: str
    weight: float = 1.0
    quotas: tuple[TierQuotaSpec, ...] = ()
    budgets: tuple[TierBudgetSpec, ...] = ()
    labels: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise TierError("tier name must be non-empty")
        if self.weight <= 0:
            raise TierError("tier weight must be positive")


@dataclass
class TierCatalog:
    _tiers: dict[str, Tier] = field(default_factory=dict)

    def register(self, tier: Tier) -> None:
        if tier.name in self._tiers:
            raise TierError(f"duplicate tier: {tier.name}")
        self._tiers[tier.name] = tier

    def get(self, name: str) -> Tier:
        try:
            return self._tiers[name]
        except KeyError as exc:
            raise TierError(f"unknown tier: {name}") from exc

    def names(self) -> list[str]:
        return sorted(self._tiers)

    def apply(self, store: Store, tenant_id: str, tier_name: str) -> Tenant:
        tier = self.get(tier_name)
        labels = dict(tier.labels)
        labels["tier"] = tier.name
        tenant = Tenant(id=tenant_id, weight=tier.weight, labels=labels)
        store.put_tenant(tenant)
        for quota_spec in tier.quotas:
            store.put_quota(
                Quota(
                    tenant_id=tenant_id,
                    resource=quota_spec.resource,
                    limit=quota_spec.limit,
                    softness=quota_spec.softness,
                )
            )
        for budget_spec in tier.budgets:
            store.put_budget(
                Budget(
                    tenant_id=tenant_id,
                    resource=budget_spec.resource,
                    allowance=budget_spec.allowance,
                    window_seconds=budget_spec.window_seconds,
                    softness=budget_spec.softness,
                )
            )
        return tenant


def default_saas_tiers() -> TierCatalog:
    catalog = TierCatalog()
    catalog.register(
        Tier(
            name="free",
            weight=1.0,
            quotas=(TierQuotaSpec("api_calls", limit=1000),),
            budgets=(TierBudgetSpec("api_calls", allowance=100, window_seconds=3600),),
            labels={"plan": "free"},
        )
    )
    catalog.register(
        Tier(
            name="pro",
            weight=2.0,
            quotas=(TierQuotaSpec("api_calls", limit=10000),),
            budgets=(TierBudgetSpec("api_calls", allowance=1000, window_seconds=3600),),
            labels={"plan": "pro"},
        )
    )
    catalog.register(
        Tier(
            name="enterprise",
            weight=5.0,
            quotas=(
                TierQuotaSpec("api_calls", limit=100000),
                TierQuotaSpec("seats", limit=500),
            ),
            budgets=(
                TierBudgetSpec("api_calls", allowance=20000, window_seconds=3600),
            ),
            labels={"plan": "enterprise"},
        )
    )
    return catalog


def compare_tiers(left: Tier, right: Tier, resource: str) -> int:
    left_limit = next((item.limit for item in left.quotas if item.resource == resource), 0.0)
    right_limit = next((item.limit for item in right.quotas if item.resource == resource), 0.0)
    if left_limit == right_limit:
        return 0
    return 1 if left_limit > right_limit else -1
