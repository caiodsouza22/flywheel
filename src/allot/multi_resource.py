"""Allocate across multiple resources in one request."""

from __future__ import annotations

from dataclasses import dataclass

from allot.engine import AllocationEngine
from allot.models import AllocationDecision, AllocationRequest, DecisionKind


@dataclass(frozen=True, slots=True)
class ResourceAmount:
    resource: str
    amount: float

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError("amount must be positive")
        if not self.resource:
            raise ValueError("resource must be non-empty")


@dataclass(frozen=True, slots=True)
class MultiResourceRequest:
    tenant_id: str
    items: tuple[ResourceAmount, ...]
    allow_partial: bool = False

    def __post_init__(self) -> None:
        if not self.tenant_id:
            raise ValueError("tenant_id must be non-empty")
        if not self.items:
            raise ValueError("items must be non-empty")


@dataclass(frozen=True, slots=True)
class MultiResourceDecision:
    tenant_id: str
    decisions: tuple[AllocationDecision, ...]

    @property
    def kind(self) -> DecisionKind:
        if all(item.kind is DecisionKind.GRANTED for item in self.decisions):
            return DecisionKind.GRANTED
        if all(item.kind is DecisionKind.DENIED for item in self.decisions):
            return DecisionKind.DENIED
        return DecisionKind.PARTIAL


class MultiResourceAllocator:
    """Fan-out a multi-resource request into per-resource engine calls."""

    def __init__(self, engine: AllocationEngine) -> None:
        self._engine = engine

    def allocate(self, request: MultiResourceRequest) -> MultiResourceDecision:
        decisions: list[AllocationDecision] = []
        for item in request.items:
            decision = self._engine.allocate(
                AllocationRequest(
                    tenant_id=request.tenant_id,
                    resource=item.resource,
                    amount=item.amount,
                    allow_partial=request.allow_partial,
                )
            )
            decisions.append(decision)
            if decision.kind is DecisionKind.DENIED and not request.allow_partial:
                # Still collect remaining as denied placeholders for visibility.
                for leftover in request.items[len(decisions) :]:
                    decisions.append(
                        AllocationDecision(
                            kind=DecisionKind.DENIED,
                            tenant_id=request.tenant_id,
                            resource=leftover.resource,
                            requested=leftover.amount,
                            granted=0.0,
                            reason="aborted_after_denial",
                        )
                    )
                break
        return MultiResourceDecision(tenant_id=request.tenant_id, decisions=tuple(decisions))
