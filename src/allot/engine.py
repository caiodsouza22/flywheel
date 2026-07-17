"""Allocation engine that evaluates requests against store state."""

from __future__ import annotations

from allot.clock import Clock, SystemClock
from allot.models import (
    AllocationDecision,
    AllocationRequest,
    DecisionKind,
    Softness,
)
from allot.policies import Policy, PolicyContext, StrictPolicy
from allot.store import Store, UsageKey
from allot.windows import FixedWindow


class AllocationEngine:
    """Coordinates quotas, budgets, pool capacity, and a contention policy."""

    def __init__(
        self,
        store: Store,
        *,
        policy: Policy | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._store = store
        self._policy = policy or StrictPolicy()
        self._clock = clock or SystemClock()

    @property
    def store(self) -> Store:
        return self._store

    @property
    def policy(self) -> Policy:
        return self._policy

    def allocate(self, request: AllocationRequest) -> AllocationDecision:
        tenant = self._store.get_tenant(request.tenant_id)
        resource = self._store.get_resource(request.resource)
        now = self._clock.now()

        quota = self._store.get_quota(request.tenant_id, request.resource)
        budget = self._store.get_budget(request.tenant_id, request.resource)

        remaining_quota: float | None = None
        softness = Softness.HARD
        if quota is not None:
            softness = quota.softness
            # Lifetime quota: empty window key aggregates all time.
            lifetime_key = UsageKey(request.tenant_id, request.resource, "lifetime")
            used = self._store.get_usage(lifetime_key)
            remaining_quota = max(0.0, quota.limit - used)

        remaining_budget: float | None = None
        budget_key: UsageKey | None = None
        if budget is not None:
            softness = budget.softness if quota is None else softness
            window = FixedWindow(size_seconds=budget.window_seconds)
            bounds = window.bounds_at(now)
            budget_key = UsageKey(
                request.tenant_id,
                request.resource,
                bounds.start.isoformat(),
            )
            used_budget = self._store.get_usage(budget_key)
            remaining_budget = max(0.0, budget.allowance - used_budget)

        remaining_pool: float | None = None
        if resource.capacity is not None:
            pool_key = UsageKey("*", request.resource, "lifetime")
            used_pool = self._store.get_usage(pool_key)
            remaining_pool = max(0.0, resource.capacity - used_pool)

        result = self._policy.decide(
            PolicyContext(
                tenant=tenant,
                requested=request.amount,
                remaining_quota=remaining_quota,
                remaining_budget=remaining_budget,
                remaining_pool=remaining_pool,
                softness=softness,
            )
        )

        granted = result.granted
        if granted <= 0:
            return AllocationDecision(
                kind=DecisionKind.DENIED,
                tenant_id=request.tenant_id,
                resource=request.resource,
                requested=request.amount,
                granted=0.0,
                remaining_quota=remaining_quota,
                reason=result.reason or "denied",
            )

        if granted < request.amount and not request.allow_partial:
            return AllocationDecision(
                kind=DecisionKind.DENIED,
                tenant_id=request.tenant_id,
                resource=request.resource,
                requested=request.amount,
                granted=0.0,
                remaining_quota=remaining_quota,
                reason=result.reason or "partial_not_allowed",
            )

        # Commit usage.
        if quota is not None and granted > 0:
            lifetime_key = UsageKey(request.tenant_id, request.resource, "lifetime")
            new_total = self._store.add_usage(lifetime_key, granted)
            remaining_quota = max(0.0, quota.limit - new_total)

        if budget_key is not None and granted > 0:
            self._store.add_usage(budget_key, granted)

        if resource.capacity is not None and granted > 0:
            pool_key = UsageKey("*", request.resource, "lifetime")
            self._store.add_usage(pool_key, granted)

        kind = DecisionKind.GRANTED if granted == request.amount else DecisionKind.PARTIAL
        return AllocationDecision(
            kind=kind,
            tenant_id=request.tenant_id,
            resource=request.resource,
            requested=request.amount,
            granted=granted,
            remaining_quota=remaining_quota,
            reason=result.reason,
        )
