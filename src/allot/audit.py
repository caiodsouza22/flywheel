"""Append-only audit trail for allocation decisions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Iterable

from allot.models import AllocationDecision, AllocationRequest


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """A recorded allocation attempt and its outcome."""

    at: datetime
    request: AllocationRequest
    decision: AllocationDecision

    def to_dict(self) -> dict[str, Any]:
        return {
            "at": self.at.isoformat(),
            "request": asdict(self.request),
            "decision": asdict(self.decision),
        }


@dataclass
class AuditLog:
    """In-memory audit log suitable for tests and single-process apps."""

    _events: list[AuditEvent] = field(default_factory=list)
    _lock: RLock = field(default_factory=RLock)

    def record(
        self,
        request: AllocationRequest,
        decision: AllocationDecision,
        *,
        at: datetime | None = None,
    ) -> AuditEvent:
        instant = at or datetime.now(timezone.utc)
        if instant.tzinfo is None:
            raise ValueError("audit timestamp must be timezone-aware")
        event = AuditEvent(at=instant, request=request, decision=decision)
        with self._lock:
            self._events.append(event)
        return event

    def __len__(self) -> int:
        with self._lock:
            return len(self._events)

    def events(self) -> list[AuditEvent]:
        with self._lock:
            return list(self._events)

    def for_tenant(self, tenant_id: str) -> list[AuditEvent]:
        with self._lock:
            return [e for e in self._events if e.request.tenant_id == tenant_id]

    def clear(self) -> None:
        with self._lock:
            self._events.clear()

    def extend(self, events: Iterable[AuditEvent]) -> None:
        with self._lock:
            self._events.extend(events)
