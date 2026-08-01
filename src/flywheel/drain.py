"""Drain helpers for clearing pending queue work."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any

from flywheel.models import Job, JobState


@dataclass
class Drain:
    """Collect and cancel pending jobs during maintenance windows."""

    name: str = "drain"
    _lock: RLock = field(default_factory=RLock, repr=False)
    _cancelled: list[str] = field(default_factory=list, repr=False)

    def cancel_pending(self, jobs: list[Job]) -> list[Job]:
        out: list[Job] = []
        with self._lock:
            for job in jobs:
                if job.state is JobState.PENDING:
                    self._cancelled.append(job.job_id)
                    out.append(Job(
                        job_id=job.job_id,
                        queue=job.queue,
                        payload=dict(job.payload),
                        tenant_id=job.tenant_id,
                        priority=job.priority,
                        state=JobState.CANCELLED,
                        attempts=job.attempts,
                        max_attempts=job.max_attempts,
                        metadata=dict(job.metadata),
                    ))
        return out

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {"name": self.name, "cancelled": len(self._cancelled)}