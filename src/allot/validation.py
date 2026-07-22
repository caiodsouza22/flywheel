"""Request and configuration validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from allot.errors import AllotError, UnknownResource, UnknownTenant
from allot.models import AllocationRequest, Budget, Quota, Resource, Tenant
from allot.store import Store


class ValidationError(AllotError):
    def __init__(self, message: str, *, path: str | None = None) -> None:
        self.path = path
        suffix = f" ({path})" if path else ""
        super().__init__(f"{message}{suffix}")


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    path: str
    message: str


@dataclass(frozen=True, slots=True)
class ValidationReport:
    issues: tuple[ValidationIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues


def validate_request(request: AllocationRequest, store: Store) -> None:
    if request.amount <= 0:
        raise ValidationError("amount must be positive", path="amount")
    try:
        store.get_tenant(request.tenant_id)
    except UnknownTenant as exc:
        raise ValidationError(f"unknown tenant: {request.tenant_id}", path="tenant_id") from exc
    try:
        store.get_resource(request.resource)
    except UnknownResource as exc:
        raise ValidationError(f"unknown resource: {request.resource}", path="resource") from exc


def validate_store_graph(store: Store) -> ValidationReport:
    issues: list[ValidationIssue] = []
    tenants = {tenant.id: tenant for tenant in store.list_tenants()}
    resources = {resource.name: resource for resource in store.list_resources()}

    for tenant in tenants.values():
        if tenant.weight <= 0:
            issues.append(ValidationIssue(f"tenants.{tenant.id}", "weight must be positive"))

    for resource in resources.values():
        if resource.capacity is not None and resource.capacity < 0:
            issues.append(
                ValidationIssue(f"resources.{resource.name}", "capacity cannot be negative")
            )

    for tenant_id in tenants:
        for resource_name in resources:
            quota = store.get_quota(tenant_id, resource_name)
            if quota is not None and quota.limit < 0:
                issues.append(
                    ValidationIssue(
                        f"quotas.{tenant_id}.{resource_name}",
                        "limit cannot be negative",
                    )
                )
            budget = store.get_budget(tenant_id, resource_name)
            if budget is not None:
                if budget.allowance < 0:
                    issues.append(
                        ValidationIssue(
                            f"budgets.{tenant_id}.{resource_name}",
                            "allowance cannot be negative",
                        )
                    )
                if budget.window_seconds <= 0:
                    issues.append(
                        ValidationIssue(
                            f"budgets.{tenant_id}.{resource_name}",
                            "window_seconds must be positive",
                        )
                    )

    return ValidationReport(issues=tuple(issues))


def assert_unique_tenants(tenants: Iterable[Tenant]) -> None:
    seen: set[str] = set()
    for tenant in tenants:
        if tenant.id in seen:
            raise ValidationError(f"duplicate tenant id: {tenant.id}", path="tenants")
        seen.add(tenant.id)


def assert_unique_resources(resources: Iterable[Resource]) -> None:
    seen: set[str] = set()
    for resource in resources:
        if resource.name in seen:
            raise ValidationError(f"duplicate resource name: {resource.name}", path="resources")
        seen.add(resource.name)


def quota_references_exist(quota: Quota, store: Store) -> bool:
    try:
        store.get_tenant(quota.tenant_id)
        store.get_resource(quota.resource)
    except (UnknownTenant, UnknownResource):
        return False
    return True


def budget_references_exist(budget: Budget, store: Store) -> bool:
    try:
        store.get_tenant(budget.tenant_id)
        store.get_resource(budget.resource)
    except (UnknownTenant, UnknownResource):
        return False
    return True
