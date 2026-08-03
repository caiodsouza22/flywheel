"""Additional contention policies beyond the core set."""

from __future__ import annotations

from dataclasses import dataclass

from allot.models import Softness
from allot.policies import Policy, PolicyContext, PolicyResult


@dataclass(frozen=True, slots=True)
class ReserveHeadroomPolicy(Policy):
    """Always keep a fraction of remaining capacity unallocated."""

    headroom_ratio: float = 0.1

    def __post_init__(self) -> None:
        if not 0 <= self.headroom_ratio < 1:
            raise ValueError("headroom_ratio must be within [0, 1)")

    def decide(self, ctx: PolicyContext) -> PolicyResult:
        ceilings: list[float] = []
        for value, soft_check in (
            (ctx.remaining_quota, True),
            (ctx.remaining_budget, True),
            (ctx.remaining_pool, False),
        ):
            if value is None:
                continue
            if soft_check and ctx.softness is Softness.SOFT:
                continue
            usable = value * (1.0 - self.headroom_ratio)
            ceilings.append(usable)
        if not ceilings:
            return PolicyResult(granted=ctx.requested)
        available = min(ceilings)
        if available >= ctx.requested:
            return PolicyResult(granted=ctx.requested)
        if available <= 0:
            return PolicyResult(granted=0.0, reason="headroom_exhausted")
        return PolicyResult(granted=0.0, reason="insufficient_after_headroom")


@dataclass(frozen=True, slots=True)
class PreferTenantPolicy(Policy):
    """Prefer a specific tenant when pool capacity is contested."""

    preferred_tenant_id: str
    inner: Policy

    def decide(self, ctx: PolicyContext) -> PolicyResult:
        if ctx.tenant.id == self.preferred_tenant_id:
            return self.inner.decide(ctx)
        # Non-preferred tenants see reduced pool.
        reduced_pool = None
        if ctx.remaining_pool is not None:
            reduced_pool = ctx.remaining_pool * 0.5
        reduced = PolicyContext(
            tenant=ctx.tenant,
            requested=ctx.requested,
            remaining_quota=ctx.remaining_quota,
            remaining_budget=ctx.remaining_budget,
            remaining_pool=reduced_pool,
            softness=ctx.softness,
        )
        return self.inner.decide(reduced)


@dataclass(frozen=True, slots=True)
class CapPolicy(Policy):
    """Hard-cap grants at a fixed maximum amount per request."""

    max_grant: float
    inner: Policy

    def __post_init__(self) -> None:
        if self.max_grant <= 0:
            raise ValueError("max_grant must be positive")

    def decide(self, ctx: PolicyContext) -> PolicyResult:
        capped_request = min(ctx.requested, self.max_grant)
        capped_ctx = PolicyContext(
            tenant=ctx.tenant,
            requested=capped_request,
            remaining_quota=ctx.remaining_quota,
            remaining_budget=ctx.remaining_budget,
            remaining_pool=ctx.remaining_pool,
            softness=ctx.softness,
        )
        result = self.inner.decide(capped_ctx)
        if result.granted <= 0:
            return result
        if capped_request < ctx.requested and result.granted == capped_request:
            return PolicyResult(granted=result.granted, reason="capped")
        return result


@dataclass(frozen=True, slots=True)
class AllOrNothingPolicy(Policy):
    """Never return partial grants from the policy layer."""

    inner: Policy

    def decide(self, ctx: PolicyContext) -> PolicyResult:
        result = self.inner.decide(ctx)
        if 0 < result.granted < ctx.requested:
            return PolicyResult(granted=0.0, reason="all_or_nothing")
        return result
