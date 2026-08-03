"""Tenure tracking for long-held leases."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any


@dataclass
class TenureTracker:
    """Tracks how long each job has been leased."""

    name: str = "tenure"
    _lock: RLock = field(default_factory=RLock, repr=False)
    _started: dict[str, datetime] = field(default_factory=dict, repr=False)

    def mark_leased(self, job_id: str, *, now: datetime | None = None) -> None:
        with self._lock:
            self._started[job_id] = now or datetime.now(timezone.utc)

    def clear(self, job_id: str) -> None:
        with self._lock:
            self._started.pop(job_id, None)

    def age_seconds(self, job_id: str, *, now: datetime | None = None) -> float | None:
        with self._lock:
            started = self._started.get(job_id)
            if started is None:
                return None
            current = now or datetime.now(timezone.utc)
            return max(0.0, (current - started).total_seconds())

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {"name": self.name, "tracked": len(self._started)}