"""Domain errors for flywheel queues and workers."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Any, Callable, Iterable, Iterator, Mapping
from uuid import uuid4

class FlywheelError(Exception):
    """Base error for the flywheel library."""

class JobNotFound(FlywheelError):
    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f'job not found: {job_id}')

class QueueNotFound(FlywheelError):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f'queue not found: {name}')

class LeaseLost(FlywheelError):
    def __init__(self, job_id: str, token: str) -> None:
        self.job_id = job_id
        self.token = token
        super().__init__(f'lease lost for job={job_id}')

class EnqueueRejected(FlywheelError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)

class HandlerFailed(FlywheelError):
    def __init__(self, job_id: str, cause: str) -> None:
        self.job_id = job_id
        self.cause = cause
        super().__init__(f'handler failed for {job_id}: {cause}')

class RetryExhausted(FlywheelError):
    def __init__(self, job_id: str, attempts: int) -> None:
        self.job_id = job_id
        self.attempts = attempts
        super().__init__(f'retries exhausted for {job_id} after {attempts}')

class ConfigurationError(FlywheelError):
    pass

class DuplicateJob(FlywheelError):
    def __init__(self, dedupe_key: str) -> None:
        self.dedupe_key = dedupe_key
        super().__init__(f'duplicate job key: {dedupe_key}')

