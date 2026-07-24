"""Budget rollover helpers for unused allowance."""

from __future__ import annotations

from dataclasses import dataclass

from allot.models import Budget, Softness


@dataclass(frozen=True, slots=True)
class RolloverRule:
    """How unused budget carries into the next window."""

    max_rollover: float
    decay: float = 1.0

    def __post_init__(self) -> None:
        if self.max_rollover < 0:
            raise ValueError("max_rollover cannot be negative")
        if not 0 <= self.decay <= 1:
            raise ValueError("decay must be within [0, 1]")

    def next_allowance(self, budget: Budget, unused: float) -> float:
        if unused < 0:
            raise ValueError("unused cannot be negative")
        carry = min(self.max_rollover, unused * self.decay)
        return budget.allowance + carry


def apply_rollover(budget: Budget, unused: float, rule: RolloverRule) -> Budget:
    return Budget(
        tenant_id=budget.tenant_id,
        resource=budget.resource,
        allowance=rule.next_allowance(budget, unused),
        window_seconds=budget.window_seconds,
        softness=budget.softness if isinstance(budget.softness, Softness) else Softness(budget.softness),
    )
