"""Tests for CSV export helpers."""

from __future__ import annotations

from allot import AllocationDecision, DecisionKind, InMemoryStore
from allot.export import decisions_to_csv, usage_to_csv
from allot.store import UsageKey


def test_decisions_to_csv() -> None:
    text = decisions_to_csv(
        [
            AllocationDecision(
                kind=DecisionKind.GRANTED,
                tenant_id="acme",
                resource="api",
                requested=2,
                granted=2,
            )
        ]
    )
    assert "tenant_id,resource" in text or "kind,tenant_id" in text
    assert "acme" in text
    assert "granted" in text


def test_usage_to_csv() -> None:
    store = InMemoryStore()
    key = UsageKey("acme", "api", "lifetime")
    store.add_usage(key, 4)
    text = usage_to_csv(store, [key])
    assert "acme" in text
    assert "4" in text
