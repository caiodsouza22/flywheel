"""Load simulation helpers for exercising allocation under synthetic traffic."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator

from allot.clock import FrozenClock
from allot.engine import AllocationEngine
from allot.models import AllocationDecision, AllocationRequest, DecisionKind, Tenant


@dataclass(frozen=True, slots=True)
class TrafficPoint:
    tenant_id: str
    resource: str
    amount: float
    at_offset_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError("amount must be positive")
        if self.at_offset_seconds < 0:
            raise ValueError("at_offset_seconds cannot be negative")


@dataclass(frozen=True, slots=True)
class SimulationStep:
    offset_seconds: float
    request: AllocationRequest
    decision: AllocationDecision


@dataclass
class SimulationReport:
    steps: list[SimulationStep] = field(default_factory=list)

    @property
    def granted_total(self) -> float:
        return sum(step.decision.granted for step in self.steps)

    @property
    def denied_count(self) -> int:
        return sum(1 for step in self.steps if step.decision.kind is DecisionKind.DENIED)

    @property
    def granted_count(self) -> int:
        return sum(1 for step in self.steps if step.decision.kind is DecisionKind.GRANTED)

    def by_tenant(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for step in self.steps:
            out[step.request.tenant_id] = (
                out.get(step.request.tenant_id, 0.0) + step.decision.granted
            )
        return out

    def denial_rate(self) -> float:
        if not self.steps:
            return 0.0
        return self.denied_count / len(self.steps)


class TrafficPattern:
    def generate(self) -> Iterator[TrafficPoint]:
        raise NotImplementedError


@dataclass
class ConstantRatePattern(TrafficPattern):
    tenant_id: str
    resource: str
    amount: float
    every_seconds: float
    count: int

    def generate(self) -> Iterator[TrafficPoint]:
        for index in range(self.count):
            yield TrafficPoint(
                tenant_id=self.tenant_id,
                resource=self.resource,
                amount=self.amount,
                at_offset_seconds=index * self.every_seconds,
            )


@dataclass
class BurstPattern(TrafficPattern):
    tenant_id: str
    resource: str
    amount: float
    burst_size: int
    gap_seconds: float = 0.0

    def generate(self) -> Iterator[TrafficPoint]:
        for index in range(self.burst_size):
            yield TrafficPoint(
                tenant_id=self.tenant_id,
                resource=self.resource,
                amount=self.amount,
                at_offset_seconds=index * self.gap_seconds,
            )


@dataclass
class MixedPattern(TrafficPattern):
    patterns: list[TrafficPattern]

    def generate(self) -> Iterator[TrafficPoint]:
        for pattern in self.patterns:
            yield from pattern.generate()


@dataclass
class LoadSimulator:
    engine: AllocationEngine
    clock: FrozenClock
    start: datetime

    def __post_init__(self) -> None:
        self.clock.set(self.start)

    def run(self, pattern: TrafficPattern) -> SimulationReport:
        points = sorted(pattern.generate(), key=lambda point: point.at_offset_seconds)
        report = SimulationReport()
        for point in points:
            self.clock.set(self.start)
            self.clock.advance(point.at_offset_seconds)
            request = AllocationRequest(
                tenant_id=point.tenant_id,
                resource=point.resource,
                amount=point.amount,
            )
            decision = self.engine.allocate(request)
            report.steps.append(
                SimulationStep(
                    offset_seconds=point.at_offset_seconds,
                    request=request,
                    decision=decision,
                )
            )
        return report


def weighted_round_robin(
    tenants: list[Tenant],
    *,
    resource: str,
    amount: float,
    ticks: int,
) -> list[TrafficPoint]:
    if ticks < 1:
        raise ValueError("ticks must be >= 1")
    if not tenants:
        raise ValueError("tenants must be non-empty")
    points: list[TrafficPoint] = []
    weights = [max(1, int(tenant.weight)) for tenant in tenants]
    cursor = 0
    produced = 0
    while produced < ticks:
        tenant = tenants[cursor % len(tenants)]
        reps = weights[cursor % len(tenants)]
        for _ in range(reps):
            if produced >= ticks:
                break
            points.append(
                TrafficPoint(
                    tenant_id=tenant.id,
                    resource=resource,
                    amount=amount,
                    at_offset_seconds=float(produced),
                )
            )
            produced += 1
        cursor += 1
    return points


def summarize_decisions(decisions: list[AllocationDecision]) -> dict[str, float]:
    return {
        "granted_total": sum(item.granted for item in decisions),
        "requested_total": sum(item.requested for item in decisions),
        "denied": float(sum(1 for item in decisions if item.kind is DecisionKind.DENIED)),
        "partial": float(sum(1 for item in decisions if item.kind is DecisionKind.PARTIAL)),
        "granted": float(sum(1 for item in decisions if item.kind is DecisionKind.GRANTED)),
    }
