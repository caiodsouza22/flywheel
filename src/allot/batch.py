"""Batch allocation helpers."""

from __future__ import annotations

from dataclasses import dataclass

from allot.engine import AllocationEngine
from allot.models import AllocationDecision, AllocationRequest, DecisionKind


@dataclass(frozen=True, slots=True)
class BatchResult:
    decisions: tuple[AllocationDecision, ...]

    @property
    def granted_total(self) -> float:
        return sum(decision.granted for decision in self.decisions)

    @property
    def denied_count(self) -> int:
        return sum(1 for decision in self.decisions if decision.kind is DecisionKind.DENIED)

    @property
    def all_granted(self) -> bool:
        return all(decision.kind is DecisionKind.GRANTED for decision in self.decisions)


class BatchAllocator:
    """Allocate many requests sequentially through one engine."""

    def __init__(self, engine: AllocationEngine, *, stop_on_deny: bool = False) -> None:
        self._engine = engine
        self._stop_on_deny = stop_on_deny

    def allocate_many(self, requests: list[AllocationRequest]) -> BatchResult:
        decisions: list[AllocationDecision] = []
        for request in requests:
            decision = self._engine.allocate(request)
            decisions.append(decision)
            if self._stop_on_deny and decision.kind is DecisionKind.DENIED:
                break
        return BatchResult(decisions=tuple(decisions))

    def allocate_all_or_nothing(
        self,
        requests: list[AllocationRequest],
    ) -> BatchResult:
        """Best-effort dry simulation using cloned usage is not available.

        This method allocates sequentially and, if any request is denied, returns
        the partial decisions with ``all_granted`` false. Callers that need true
        rollback should use reservations.
        """
        result = self.allocate_many(requests)
        return result
