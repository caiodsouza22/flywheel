"""Tenant hierarchy helpers for inherited quotas and weights."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock

from allot.errors import AllotError, UnknownTenant
from allot.models import Tenant


class HierarchyError(AllotError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


@dataclass
class TenantNode:
    tenant: Tenant
    parent_id: str | None = None
    children: set[str] = field(default_factory=set)


class TenantHierarchy:
    """Forest of tenants with parent/child relationships."""

    def __init__(self) -> None:
        self._nodes: dict[str, TenantNode] = {}
        self._lock = RLock()

    def add(self, tenant: Tenant, *, parent_id: str | None = None) -> None:
        with self._lock:
            if tenant.id in self._nodes:
                raise HierarchyError(f"tenant already registered: {tenant.id}")
            if parent_id is not None:
                parent = self._nodes.get(parent_id)
                if parent is None:
                    raise UnknownTenant(parent_id)
                parent.children.add(tenant.id)
            self._nodes[tenant.id] = TenantNode(tenant=tenant, parent_id=parent_id)

    def get(self, tenant_id: str) -> Tenant:
        with self._lock:
            node = self._nodes.get(tenant_id)
            if node is None:
                raise UnknownTenant(tenant_id)
            return node.tenant

    def parent(self, tenant_id: str) -> Tenant | None:
        with self._lock:
            node = self._require(tenant_id)
            if node.parent_id is None:
                return None
            return self._nodes[node.parent_id].tenant

    def children(self, tenant_id: str) -> list[Tenant]:
        with self._lock:
            node = self._require(tenant_id)
            return [self._nodes[child_id].tenant for child_id in sorted(node.children)]

    def ancestors(self, tenant_id: str) -> list[Tenant]:
        with self._lock:
            self._require(tenant_id)
            result: list[Tenant] = []
            current = self._nodes[tenant_id].parent_id
            seen: set[str] = set()
            while current is not None:
                if current in seen:
                    raise HierarchyError(f"cycle detected at {current}")
                seen.add(current)
                node = self._nodes[current]
                result.append(node.tenant)
                current = node.parent_id
            return result

    def descendants(self, tenant_id: str) -> list[Tenant]:
        with self._lock:
            self._require(tenant_id)
            out: list[Tenant] = []
            stack = list(self._nodes[tenant_id].children)
            seen: set[str] = set()
            while stack:
                child_id = stack.pop()
                if child_id in seen:
                    raise HierarchyError(f"cycle detected at {child_id}")
                seen.add(child_id)
                node = self._nodes[child_id]
                out.append(node.tenant)
                stack.extend(node.children)
            return sorted(out, key=lambda tenant: tenant.id)

    def effective_weight(self, tenant_id: str) -> float:
        """Product of tenant weight and all ancestor weights."""
        with self._lock:
            node = self._require(tenant_id)
            weight = node.tenant.weight
            for ancestor in self.ancestors(tenant_id):
                weight *= ancestor.weight
            return weight

    def roots(self) -> list[Tenant]:
        with self._lock:
            return [
                node.tenant
                for node in sorted(self._nodes.values(), key=lambda item: item.tenant.id)
                if node.parent_id is None
            ]

    def _require(self, tenant_id: str) -> TenantNode:
        node = self._nodes.get(tenant_id)
        if node is None:
            raise UnknownTenant(tenant_id)
        return node
