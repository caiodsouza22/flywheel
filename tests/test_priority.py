"""Tests for priority helpers."""

from __future__ import annotations

from allot import Tenant
from allot.priority import Priority, PrioritizedTenant, sort_by_priority


def test_sort_by_priority() -> None:
    items = [
        PrioritizedTenant(Tenant(id="a", weight=1), Priority.LOW),
        PrioritizedTenant(Tenant(id="b", weight=1), Priority.CRITICAL),
        PrioritizedTenant(Tenant(id="c", weight=5), Priority.NORMAL),
    ]
    ordered = sort_by_priority(items)
    assert [item.tenant.id for item in ordered] == ["b", "c", "a"]
    assert ordered[0].effective_weight == float(Priority.CRITICAL)
