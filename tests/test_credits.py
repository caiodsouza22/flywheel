"""Tests for prepaid credits."""

from __future__ import annotations

import pytest

from allot.credits import CreditLedger, InsufficientCredits


def test_deposit_charge_transfer() -> None:
    ledger = CreditLedger()
    ledger.open("a", balance=10)
    ledger.open("b", balance=0)
    ledger.deposit("a", 5)
    assert ledger.charge("a", 3) == 12
    ledger.transfer("a", "b", 4)
    assert ledger.balances() == {"a": 8.0, "b": 4.0}


def test_insufficient_credits() -> None:
    ledger = CreditLedger()
    ledger.open("a", balance=1)
    with pytest.raises(InsufficientCredits):
        ledger.charge("a", 2)
