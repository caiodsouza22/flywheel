"""Tests for tenant hierarchy."""

from __future__ import annotations

import pytest

from allot import Tenant, UnknownTenant
from allot.hierarchy import HierarchyError, TenantHierarchy


def test_ancestors_descendants_and_weights() -> None:
    tree = TenantHierarchy()
    tree.add(Tenant(id="root", weight=2.0))
    tree.add(Tenant(id="child", weight=3.0), parent_id="root")
    tree.add(Tenant(id="leaf", weight=1.0), parent_id="child")
    assert [t.id for t in tree.ancestors("leaf")] == ["child", "root"]
    assert [t.id for t in tree.descendants("root")] == ["child", "leaf"]
    assert tree.effective_weight("leaf") == 6.0
    assert tree.roots()[0].id == "root"
    assert tree.parent("child").id == "root"
    assert tree.children("root")[0].id == "child"


def test_unknown_parent() -> None:
    tree = TenantHierarchy()
    with pytest.raises(UnknownTenant):
        tree.add(Tenant(id="x"), parent_id="missing")


def test_duplicate_tenant() -> None:
    tree = TenantHierarchy()
    tree.add(Tenant(id="a"))
    with pytest.raises(HierarchyError):
        tree.add(Tenant(id="a"))
