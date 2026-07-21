"""Tests for sliding-window budget accounting."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from allot import (
    FrozenClock,
    InsufficientSlidingBudget,
    SlidingBudgetAccount,
    SlidingBudgetLedger,
    Softness,
)


def test_spend_and_prune_outside_window() -> None:
    clock = FrozenClock(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc))
    account = SlidingBudgetAccount(
        tenant_id="acme",
        resource="api",
        allowance=10,
        window_seconds=60,
    )
    account.spend(4, clock.now())
    assert account.remaining(clock.now()) == 6
    clock.advance(61)
    assert account.spent_in_window(clock.now()) == 0
    assert account.remaining(clock.now()) == 10


def test_hard_budget_blocks_overspend() -> None:
    now = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    account = SlidingBudgetAccount(
        tenant_id="acme",
        resource="api",
        allowance=5,
        window_seconds=30,
        softness=Softness.HARD,
    )
    account.spend(5, now)
    with pytest.raises(InsufficientSlidingBudget):
        account.spend(1, now)


def test_soft_budget_allows_overspend() -> None:
    now = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    account = SlidingBudgetAccount(
        tenant_id="acme",
        resource="api",
        allowance=5,
        window_seconds=30,
        softness=Softness.SOFT,
    )
    account.spend(5, now)
    assert account.can_spend(3, now) is True
    account.spend(3, now)
    assert account.spent_in_window(now) == 8


def test_ledger_registers_accounts() -> None:
    clock = FrozenClock(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc))
    ledger = SlidingBudgetLedger(clock=clock)
    ledger.register(
        SlidingBudgetAccount(
            tenant_id="acme",
            resource="api",
            allowance=20,
            window_seconds=60,
        )
    )
    ledger.spend("acme", "api", 5)
    assert ledger.remaining("acme", "api") == 15
