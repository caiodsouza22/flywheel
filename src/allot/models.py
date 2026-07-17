"""Core domain models for tenants, resources, quotas, and budgets."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class Softness(str, Enum):
    """Whether exceeding a limit is rejected or only recorded."""

    HARD = "hard"
    SOFT = "soft"


class DecisionKind(str, Enum):
    """Outcome of an allocation attempt."""

    GRANTED = "granted"
    PARTIAL = "partial"
    DENIED = "denied"


@dataclass(frozen=True, slots=True)
class Tenant:
    """A consumer of shared capacity."""

    id: str
    weight: float = 1.0
    labels: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("tenant id must be non-empty")
        if self.weight <= 0:
            raise ValueError("tenant weight must be positive")


@dataclass(frozen=True, slots=True)
class Resource:
    """A named capacity pool that can be allocated."""

    name: str
    unit: str = "unit"
    capacity: float | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("resource name must be non-empty")
        if self.capacity is not None and self.capacity < 0:
            raise ValueError("resource capacity cannot be negative")


@dataclass(frozen=True, slots=True)
class Quota:
    """Per-tenant ceiling on a resource."""

    tenant_id: str
    resource: str
    limit: float
    softness: Softness = Softness.HARD

    def __post_init__(self) -> None:
        if self.limit < 0:
            raise ValueError("quota limit cannot be negative")


@dataclass(frozen=True, slots=True)
class Budget:
    """Spendable allowance over an evaluation window."""

    tenant_id: str
    resource: str
    allowance: float
    window_seconds: int
    softness: Softness = Softness.HARD

    def __post_init__(self) -> None:
        if self.allowance < 0:
            raise ValueError("budget allowance cannot be negative")
        if self.window_seconds <= 0:
            raise ValueError("budget window_seconds must be positive")


@dataclass(frozen=True, slots=True)
class AllocationRequest:
    """A request to consume capacity on behalf of a tenant."""

    tenant_id: str
    resource: str
    amount: float
    allow_partial: bool = False
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError("allocation amount must be positive")


@dataclass(frozen=True, slots=True)
class AllocationDecision:
    """Result returned by the allocation engine."""

    kind: DecisionKind
    tenant_id: str
    resource: str
    requested: float
    granted: float
    remaining_quota: float | None = None
    reason: str | None = None

    @property
    def granted_fully(self) -> bool:
        return self.kind is DecisionKind.GRANTED and self.granted == self.requested
