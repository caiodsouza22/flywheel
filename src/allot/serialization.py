"""JSON-friendly serialization helpers for allot domain objects."""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Mapping

from allot.models import (
    AllocationDecision,
    AllocationRequest,
    Budget,
    DecisionKind,
    Quota,
    Resource,
    Softness,
    Tenant,
)


def _enum_value(value: Enum | str) -> str:
    return value.value if isinstance(value, Enum) else str(value)


def tenant_to_dict(tenant: Tenant) -> dict[str, Any]:
    return {
        "id": tenant.id,
        "weight": tenant.weight,
        "labels": dict(tenant.labels),
    }


def tenant_from_dict(data: Mapping[str, Any]) -> Tenant:
    return Tenant(
        id=str(data["id"]),
        weight=float(data.get("weight", 1.0)),
        labels=dict(data.get("labels", {})),
    )


def resource_to_dict(resource: Resource) -> dict[str, Any]:
    return {
        "name": resource.name,
        "unit": resource.unit,
        "capacity": resource.capacity,
    }


def resource_from_dict(data: Mapping[str, Any]) -> Resource:
    capacity = data.get("capacity")
    return Resource(
        name=str(data["name"]),
        unit=str(data.get("unit", "unit")),
        capacity=None if capacity is None else float(capacity),
    )


def quota_to_dict(quota: Quota) -> dict[str, Any]:
    return {
        "tenant_id": quota.tenant_id,
        "resource": quota.resource,
        "limit": quota.limit,
        "softness": _enum_value(quota.softness),
    }


def quota_from_dict(data: Mapping[str, Any]) -> Quota:
    return Quota(
        tenant_id=str(data["tenant_id"]),
        resource=str(data["resource"]),
        limit=float(data["limit"]),
        softness=Softness(str(data.get("softness", Softness.HARD.value))),
    )


def budget_to_dict(budget: Budget) -> dict[str, Any]:
    return {
        "tenant_id": budget.tenant_id,
        "resource": budget.resource,
        "allowance": budget.allowance,
        "window_seconds": budget.window_seconds,
        "softness": _enum_value(budget.softness),
    }


def budget_from_dict(data: Mapping[str, Any]) -> Budget:
    return Budget(
        tenant_id=str(data["tenant_id"]),
        resource=str(data["resource"]),
        allowance=float(data["allowance"]),
        window_seconds=int(data["window_seconds"]),
        softness=Softness(str(data.get("softness", Softness.HARD.value))),
    )


def request_to_dict(request: AllocationRequest) -> dict[str, Any]:
    return {
        "tenant_id": request.tenant_id,
        "resource": request.resource,
        "amount": request.amount,
        "allow_partial": request.allow_partial,
        "metadata": dict(request.metadata),
    }


def request_from_dict(data: Mapping[str, Any]) -> AllocationRequest:
    return AllocationRequest(
        tenant_id=str(data["tenant_id"]),
        resource=str(data["resource"]),
        amount=float(data["amount"]),
        allow_partial=bool(data.get("allow_partial", False)),
        metadata=dict(data.get("metadata", {})),
    )


def decision_to_dict(decision: AllocationDecision) -> dict[str, Any]:
    return {
        "kind": _enum_value(decision.kind),
        "tenant_id": decision.tenant_id,
        "resource": decision.resource,
        "requested": decision.requested,
        "granted": decision.granted,
        "remaining_quota": decision.remaining_quota,
        "reason": decision.reason,
    }


def decision_from_dict(data: Mapping[str, Any]) -> AllocationDecision:
    remaining = data.get("remaining_quota")
    return AllocationDecision(
        kind=DecisionKind(str(data["kind"])),
        tenant_id=str(data["tenant_id"]),
        resource=str(data["resource"]),
        requested=float(data["requested"]),
        granted=float(data["granted"]),
        remaining_quota=None if remaining is None else float(remaining),
        reason=data.get("reason"),
    )


def dumps(obj: Any, *, indent: int | None = None) -> str:
    """Serialize a supported allot object or nested structure to JSON text."""
    return json.dumps(to_plain(obj), indent=indent, sort_keys=True)


def loads_tenant(text: str) -> Tenant:
    return tenant_from_dict(json.loads(text))


def to_plain(obj: Any) -> Any:
    if isinstance(obj, Tenant):
        return tenant_to_dict(obj)
    if isinstance(obj, Resource):
        return resource_to_dict(obj)
    if isinstance(obj, Quota):
        return quota_to_dict(obj)
    if isinstance(obj, Budget):
        return budget_to_dict(obj)
    if isinstance(obj, AllocationRequest):
        return request_to_dict(obj)
    if isinstance(obj, AllocationDecision):
        return decision_to_dict(obj)
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, list):
        return [to_plain(item) for item in obj]
    if isinstance(obj, dict):
        return {str(key): to_plain(value) for key, value in obj.items()}
    return obj
