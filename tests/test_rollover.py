"""Tests for budget rollover."""

from __future__ import annotations

from allot import Budget
from allot.rollover import RolloverRule, apply_rollover


def test_rollover_applies_decay_and_cap() -> None:
    budget = Budget(tenant_id="acme", resource="api", allowance=100, window_seconds=60)
    rule = RolloverRule(max_rollover=20, decay=0.5)
    next_budget = apply_rollover(budget, unused=50, rule=rule)
    assert next_budget.allowance == 120
