"""Read-only store wrapper that blocks mutating operations."""

from __future__ import annotations

from allot.errors import AllotError
from allot.models import Budget, Quota, Resource, Tenant
from allot.store import Store, UsageKey


class ReadOnlyViolation(AllotError):
    def __init__(self, operation: str) -> None:
        self.operation = operation
        super().__init__(f"store is read-only; cannot {operation}")


class ReadOnlyStore(Store):
    def __init__(self, inner: Store) -> None:
        self._inner = inner

    def put_tenant(self, tenant: Tenant) -> None:
        raise ReadOnlyViolation("put_tenant")

    def get_tenant(self, tenant_id: str) -> Tenant:
        return self._inner.get_tenant(tenant_id)

    def list_tenants(self) -> list[Tenant]:
        return self._inner.list_tenants()

    def put_resource(self, resource: Resource) -> None:
        raise ReadOnlyViolation("put_resource")

    def get_resource(self, name: str) -> Resource:
        return self._inner.get_resource(name)

    def list_resources(self) -> list[Resource]:
        return self._inner.list_resources()

    def put_quota(self, quota: Quota) -> None:
        raise ReadOnlyViolation("put_quota")

    def get_quota(self, tenant_id: str, resource: str) -> Quota | None:
        return self._inner.get_quota(tenant_id, resource)

    def put_budget(self, budget: Budget) -> None:
        raise ReadOnlyViolation("put_budget")

    def get_budget(self, tenant_id: str, resource: str) -> Budget | None:
        return self._inner.get_budget(tenant_id, resource)

    def get_usage(self, key: UsageKey) -> float:
        return self._inner.get_usage(key)

    def add_usage(self, key: UsageKey, amount: float) -> float:
        raise ReadOnlyViolation("add_usage")

    def reset_usage(self, key: UsageKey) -> None:
        raise ReadOnlyViolation("reset_usage")
