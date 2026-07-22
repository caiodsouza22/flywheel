"""Overdraft policies that temporarily allow spending past hard ceilings."""

from __future__ import annotations

from dataclasses import dataclass

from allot.models import Softness
from allot.policies import Policy, PolicyContext, PolicyResult


@dataclass(frozen=True, slots=True)
class OverdraftPolicy(Policy):
    """Grant up to ``limit + overdraft`` when hard ceilings are exhausted."""

    overdraft: float = 0.0

    def __post_init__(self) -> None:
        if self.overdraft < 0:
            raise ValueError("overdraft cannot be negative")

    def decide(self, ctx: PolicyContext) -> PolicyResult:
        ceilings: list[float] = []
        if ctx.remaining_quota is not None and ctx.softness is Softness.HARD:
            ceilings.append(ctx.remaining_quota + self.overdraft)
        if ctx.remaining_budget is not None and ctx.softness is Softness.HARD:
            ceilings.append(ctx.remaining_budget + self.overdraft)
        if ctx.remaining_pool is not None:
            ceilings.append(ctx.remaining_pool + self.overdraft)

        if not ceilings:
            return PolicyResult(granted=ctx.requested)

        available = min(ceilings)
        if available >= ctx.requested:
            used_overdraft = any(
                base is not None and base < ctx.requested
                for base in (ctx.remaining_quota, ctx.remaining_budget, ctx.remaining_pool)
            )
            reason = "overdraft" if used_overdraft else None
            return PolicyResult(granted=ctx.requested, reason=reason)
        return PolicyResult(granted=0.0, reason="insufficient_capacity")
