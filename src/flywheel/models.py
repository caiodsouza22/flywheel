"""Core job, queue, and lease models."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Any, Callable, Iterable, Iterator, Mapping
from uuid import uuid4

from enum import Enum

class JobState(str, Enum):
    PENDING = 'pending'
    LEASED = 'leased'
    RUNNING = 'running'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    DEAD = 'dead'
    DELAYED = 'delayed'
    CANCELLED = 'cancelled'

@dataclass(frozen=True)
class Job:
    job_id: str
    queue: str
    payload: dict[str, Any]
    tenant_id: str = 'default'
    priority: float = 0.0
    state: JobState = JobState.PENDING
    attempts: int = 0
    max_attempts: int = 5
    available_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    dedupe_key: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_terminal(self) -> bool:
        return self.state in {JobState.SUCCEEDED, JobState.DEAD, JobState.CANCELLED}

@dataclass(frozen=True)
class Lease:
    job_id: str
    worker_id: str
    token: str
    expires_at: datetime
    fencing_token: int = 0

@dataclass(frozen=True)
class QueueSpec:
    name: str
    max_depth: int = 10_000
    default_priority: float = 0.0
    visibility_timeout_seconds: float = 30.0
    tenant_fairness: bool = True

@dataclass(frozen=True)
class AckReceipt:
    job_id: str
    state: JobState
    worker_id: str
    at: datetime
    detail: str = ''

@dataclass(frozen=True)
class EnqueueRequest:
    queue: str
    payload: dict[str, Any]
    tenant_id: str = 'default'
    priority: float | None = None
    delay_seconds: float = 0.0
    dedupe_key: str | None = None
    max_attempts: int = 5
    metadata: dict[str, Any] = field(default_factory=dict)

