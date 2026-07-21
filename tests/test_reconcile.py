"""Tests for usage reconciliation."""

from __future__ import annotations

from allot import InMemoryStore, UsageExpectation, apply_corrections, reconcile_usage
from allot.store import UsageKey


def test_reconcile_detects_drift_and_corrects() -> None:
    store = InMemoryStore()
    key = UsageKey("acme", "api", "lifetime")
    store.add_usage(key, 8)
    report = reconcile_usage(
        store,
        [UsageExpectation("acme", "api", "lifetime", expected=5)],
    )
    assert report.ok is False
    assert len(report.drifts) == 1
    assert report.drifts[0].delta == 3
    apply_corrections(store, report.drifts, mode="set_expected")
    assert store.get_usage(key) == 5
    fixed = reconcile_usage(
        store,
        [UsageExpectation("acme", "api", "lifetime", expected=5)],
    )
    assert fixed.ok is True
    assert fixed.matched == 1


def test_add_delta_correction() -> None:
    store = InMemoryStore()
    key = UsageKey("acme", "api", "lifetime")
    store.add_usage(key, 2)
    report = reconcile_usage(
        store,
        [UsageExpectation("acme", "api", "lifetime", expected=5)],
    )
    apply_corrections(store, report.drifts, mode="add_delta")
    assert store.get_usage(key) == 5
