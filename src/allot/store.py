"""Persistence of usage counters and registered configuration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from threading import RLock
from typing import Iterable

from allot.errors import UnknownResource, UnknownTenant
from allot.models import Budget, Quota, Resource, Tenant


@dataclass
class UsageKey:
    tenant_id: str
    resource: str
    window_start_iso: str


@dataclass
class UsageRecord:
    key: UsageKey
    consumed: float = 0.0


class Store(ABC):
    """Abstract registry + usage ledger."""

    @abstractmethod
    def put_tenant(self, tenant: Tenant) -> None: ...

    @abstractmethod
    def get_tenant(self, tenant_id: str) -> Tenant: ...

    @abstractmethod
    def list_tenants(self) -> list[Tenant]: ...

    @abstractmethod
    def put_resource(self, resource: Resource) -> None: ...

    @abstractmethod
    def get_resource(self, name: str) -> Resource: ...

    @abstractmethod
    def list_resources(self) -> list[Resource]: ...

    @abstractmethod
    def put_quota(self, quota: Quota) -> None: ...

    @abstractmethod
    def get_quota(self, tenant_id: str, resource: str) -> Quota | None: ...

    @abstractmethod
    def put_budget(self, budget: Budget) -> None: ...

    @abstractmethod
    def get_budget(self, tenant_id: str, resource: str) -> Budget | None: ...

    @abstractmethod
    def get_usage(self, key: UsageKey) -> float: ...

    @abstractmethod
    def add_usage(self, key: UsageKey, amount: float) -> float:
        """Atomically increase usage and return the new total."""

    @abstractmethod
    def reset_usage(self, key: UsageKey) -> None: ...


@dataclass
class InMemoryStore(Store):
    """Thread-safe in-process store for development and tests."""

    _tenants: dict[str, Tenant] = field(default_factory=dict)
    _resources: dict[str, Resource] = field(default_factory=dict)
    _quotas: dict[tuple[str, str], Quota] = field(default_factory=dict)
    _budgets: dict[tuple[str, str], Budget] = field(default_factory=dict)
    _usage: dict[tuple[str, str, str], float] = field(default_factory=dict)
    _lock: RLock = field(default_factory=RLock)

    def put_tenant(self, tenant: Tenant) -> None:
        with self._lock:
            self._tenants[tenant.id] = tenant

    def get_tenant(self, tenant_id: str) -> Tenant:
        with self._lock:
            try:
                return self._tenants[tenant_id]
            except KeyError as exc:
                raise UnknownTenant(tenant_id) from exc

    def list_tenants(self) -> list[Tenant]:
        with self._lock:
            return sorted(self._tenants.values(), key=lambda t: t.id)

    def put_resource(self, resource: Resource) -> None:
        with self._lock:
            self._resources[resource.name] = resource

    def get_resource(self, name: str) -> Resource:
        with self._lock:
            try:
                return self._resources[name]
            except KeyError as exc:
                raise UnknownResource(name) from exc

    def list_resources(self) -> list[Resource]:
        with self._lock:
            return sorted(self._resources.values(), key=lambda r: r.name)

    def put_quota(self, quota: Quota) -> None:
        with self._lock:
            self.get_tenant(quota.tenant_id)
            self.get_resource(quota.resource)
            self._quotas[(quota.tenant_id, quota.resource)] = quota

    def get_quota(self, tenant_id: str, resource: str) -> Quota | None:
        with self._lock:
            return self._quotas.get((tenant_id, resource))

    def put_budget(self, budget: Budget) -> None:
        with self._lock:
            self.get_tenant(budget.tenant_id)
            self.get_resource(budget.resource)
            self._budgets[(budget.tenant_id, budget.resource)] = budget

    def get_budget(self, tenant_id: str, resource: str) -> Budget | None:
        with self._lock:
            return self._budgets.get((tenant_id, resource))

    def get_usage(self, key: UsageKey) -> float:
        with self._lock:
            return self._usage.get((key.tenant_id, key.resource, key.window_start_iso), 0.0)

    def add_usage(self, key: UsageKey, amount: float) -> float:
        if amount < 0:
            raise ValueError("usage amount cannot be negative")
        with self._lock:
            k = (key.tenant_id, key.resource, key.window_start_iso)
            total = self._usage.get(k, 0.0) + amount
            self._usage[k] = total
            return total

    def reset_usage(self, key: UsageKey) -> None:
        with self._lock:
            self._usage.pop((key.tenant_id, key.resource, key.window_start_iso), None)

    def seed(
        self,
        *,
        tenants: Iterable[Tenant] = (),
        resources: Iterable[Resource] = (),
        quotas: Iterable[Quota] = (),
        budgets: Iterable[Budget] = (),
    ) -> None:
        for tenant in tenants:
            self.put_tenant(tenant)
        for resource in resources:
            self.put_resource(resource)
        for quota in quotas:
            self.put_quota(quota)
        for budget in budgets:
            self.put_budget(budget)
