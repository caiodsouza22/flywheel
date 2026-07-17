"""Contention policies that shape allocation decisions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from allot.models import Softness, Tenant


@dataclass(frozen=True, slots=True)
class PolicyContext:
    """Inputs available when resolving how much to grant."""

    tenant: Tenant
    requested: float
    remaining_quota: float | None
    remaining_budget: float | None
    remaining_pool: float | None
    softness: Softness


@dataclass(frozen=True, slots=True)
class PolicyResult:
    granted: float
    reason: str | None = None


class Policy(ABC):
    """Decides the granted amount given remaining capacity."""

    @abstractmethod
    def decide(self, ctx: PolicyContext) -> PolicyResult: ...


class StrictPolicy(Policy):
    """Grant fully or nothing. Soft limits never block."""

    def decide(self, ctx: PolicyContext) -> PolicyResult:
        ceilings: list[float] = []
        if ctx.remaining_quota is not None and ctx.softness is Softness.HARD:
            ceilings.append(ctx.remaining_quota)
        if ctx.remaining_budget is not None and ctx.softness is Softness.HARD:
            ceilings.append(ctx.remaining_budget)
        if ctx.remaining_pool is not None:
            ceilings.append(ctx.remaining_pool)

        if not ceilings:
            return PolicyResult(granted=ctx.requested)

        available = min(ceilings)
        if available >= ctx.requested:
            return PolicyResult(granted=ctx.requested)
        return PolicyResult(granted=0.0, reason="insufficient_capacity")


class BurstPolicy(Policy):
    """Allow a fraction of the request beyond hard ceilings."""

    def __init__(self, burst_ratio: float = 0.2) -> None:
        if burst_ratio < 0:
            raise ValueError("burst_ratio cannot be negative")
        self.burst_ratio = burst_ratio

    def decide(self, ctx: PolicyContext) -> PolicyResult:
        hard_ceilings: list[float] = []
        if ctx.remaining_quota is not None and ctx.softness is Softness.HARD:
            hard_ceilings.append(ctx.remaining_quota)
        if ctx.remaining_budget is not None and ctx.softness is Softness.HARD:
            hard_ceilings.append(ctx.remaining_budget)
        if ctx.remaining_pool is not None:
            hard_ceilings.append(ctx.remaining_pool)

        if not hard_ceilings:
            return PolicyResult(granted=ctx.requested)

        available = min(hard_ceilings)
        if available >= ctx.requested:
            return PolicyResult(granted=ctx.requested)

        burst_headroom = available * self.burst_ratio
        grantable = available + burst_headroom
        if grantable >= ctx.requested:
            return PolicyResult(granted=ctx.requested, reason="burst")
        return PolicyResult(granted=0.0, reason="insufficient_capacity")


class WeightedFairPolicy(Policy):
    """Scale the grant by tenant weight when capacity is scarce.

    When remaining pool capacity is known and below demand, the tenant may
    receive ``min(requested, pool * weight / (weight + 1))`` as a simple
    fairness heuristic. Quota/budget hard ceilings still apply.
    """

    def decide(self, ctx: PolicyContext) -> PolicyResult:
        target = ctx.requested
        if ctx.remaining_pool is not None and ctx.remaining_pool < ctx.requested:
            share = ctx.remaining_pool * (ctx.tenant.weight / (ctx.tenant.weight + 1.0))
            target = min(ctx.requested, share)

        if ctx.remaining_quota is not None and ctx.softness is Softness.HARD:
            target = min(target, ctx.remaining_quota)
        if ctx.remaining_budget is not None and ctx.softness is Softness.HARD:
            target = min(target, ctx.remaining_budget)
        if ctx.remaining_pool is not None:
            target = min(target, ctx.remaining_pool)

        if target <= 0:
            return PolicyResult(granted=0.0, reason="insufficient_capacity")
        if target < ctx.requested:
            return PolicyResult(granted=target, reason="weighted_fair_partial")
        return PolicyResult(granted=target)
