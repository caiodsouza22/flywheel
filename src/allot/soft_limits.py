"""Track soft-limit breaches without blocking allocation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import RLock

from allot.clock import Clock, SystemClock
from allot.models import AllocationDecision, AllocationRequest, Softness
from allot.store import Store, UsageKey


@dataclass(frozen=True, slots=True)
class SoftBreach:
    tenant_id: str
    resource: str
    requested: float
    remaining_before: float
    at: datetime


@dataclass
class SoftLimitTracker:
    store: Store
    _breaches: list[SoftBreach] = field(default_factory=list)
    _lock: RLock = field(default_factory=RLock)
    _clock: Clock = field(default_factory=SystemClock)

    def set_clock(self, clock: Clock) -> None:
        self._clock = clock

    def observe(
        self,
        request: AllocationRequest,
        decision: AllocationDecision,
        *,
        remaining_before: float | None = None,
    ) -> SoftBreach | None:
        quota = self.store.get_quota(request.tenant_id, request.resource)
        if quota is None or quota.softness is not Softness.SOFT:
            return None
        if remaining_before is None:
            used = self.store.get_usage(
                UsageKey(request.tenant_id, request.resource, "lifetime")
            )
            # Decision already committed; reconstruct approximate remaining before.
            remaining_before = max(0.0, quota.limit - (used - decision.granted))
        if remaining_before >= request.amount:
            return None
        breach = SoftBreach(
            tenant_id=request.tenant_id,
            resource=request.resource,
            requested=request.amount,
            remaining_before=remaining_before,
            at=self._clock.now(),
        )
        with self._lock:
            self._breaches.append(breach)
        return breach

    def breaches(self, *, tenant_id: str | None = None) -> list[SoftBreach]:
        with self._lock:
            if tenant_id is None:
                return list(self._breaches)
            return [item for item in self._breaches if item.tenant_id == tenant_id]

    def count(self) -> int:
        with self._lock:
            return len(self._breaches)

    def clear(self) -> None:
        with self._lock:
            self._breaches.clear()
