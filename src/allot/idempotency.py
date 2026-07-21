"""Idempotency keys for allocation requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import RLock

from allot.clock import Clock, SystemClock
from allot.errors import AllotError
from allot.models import AllocationDecision, AllocationRequest


class IdempotencyConflict(AllotError):
    """Raised when the same key is reused with a different request fingerprint."""

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"idempotency conflict for key={key}")


@dataclass(frozen=True, slots=True)
class IdempotencyRecord:
    key: str
    fingerprint: str
    decision: AllocationDecision
    created_at: datetime
    expires_at: datetime


def fingerprint_request(request: AllocationRequest) -> str:
    meta = ",".join(f"{k}={v}" for k, v in sorted(request.metadata.items()))
    return (
        f"{request.tenant_id}|{request.resource}|{request.amount}|"
        f"{int(request.allow_partial)}|{meta}"
    )


@dataclass
class IdempotencyStore:
    """Remembers decisions for a TTL so retries can replay safely."""

    ttl_seconds: float = 3600.0
    _records: dict[str, IdempotencyRecord] = field(default_factory=dict)
    _lock: RLock = field(default_factory=RLock)
    _clock: Clock = field(default_factory=SystemClock)

    def __post_init__(self) -> None:
        if self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")

    def set_clock(self, clock: Clock) -> None:
        self._clock = clock

    def get(self, key: str) -> IdempotencyRecord | None:
        now = self._clock.now()
        with self._lock:
            self._purge_locked(now)
            return self._records.get(key)

    def remember(
        self,
        key: str,
        request: AllocationRequest,
        decision: AllocationDecision,
    ) -> IdempotencyRecord:
        if not key:
            raise ValueError("idempotency key must be non-empty")
        now = self._clock.now()
        fp = fingerprint_request(request)
        with self._lock:
            self._purge_locked(now)
            existing = self._records.get(key)
            if existing is not None:
                if existing.fingerprint != fp:
                    raise IdempotencyConflict(key)
                return existing
            record = IdempotencyRecord(
                key=key,
                fingerprint=fp,
                decision=decision,
                created_at=now,
                expires_at=now + timedelta(seconds=self.ttl_seconds),
            )
            self._records[key] = record
            return record

    def replay_or_none(self, key: str, request: AllocationRequest) -> AllocationDecision | None:
        record = self.get(key)
        if record is None:
            return None
        if record.fingerprint != fingerprint_request(request):
            raise IdempotencyConflict(key)
        return record.decision

    def _purge_locked(self, now: datetime) -> None:
        expired = [key for key, record in self._records.items() if now >= record.expires_at]
        for key in expired:
            self._records.pop(key, None)
