"""Shard queues across partitions."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Any, Callable, Iterable, Iterator, Mapping
from uuid import uuid4

from flywheel.errors import FlywheelError, EnqueueRejected
from flywheel.models import Job, JobState, Lease, QueueSpec, AckReceipt


@dataclass
class Sharding:
    """Shard queues across partitions."""

    name: str = 'default'
    enabled: bool = True
    _lock: RLock = field(default_factory=RLock, repr=False)
    _data: dict[str, Any] = field(default_factory=dict, repr=False)
    _history: list[dict[str, Any]] = field(default_factory=list, repr=False)

    def reset(self) -> None:
        with self._lock:
            self._data.clear()
            self._history.clear()

    def record(self, event: str, **fields: Any) -> dict[str, Any]:
        row = {'event': event, 'at': datetime.now(timezone.utc).isoformat(), **fields}
        with self._lock:
            self._history.append(row)
            if len(self._history) > 5000:
                self._history = self._history[-2500:]
        return row

    def history(self, *, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._history[-limit:])

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = value
            self.record('set', key=key)

    def incr(self, key: str, amount: float = 1.0) -> float:
        with self._lock:
            cur = float(self._data.get(key, 0.0))
            nxt = cur + amount
            self._data[key] = nxt
            return nxt

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                'name': self.name,
                'enabled': self.enabled,
                'keys': sorted(self._data),
                'history_len': len(self._history),
            }

    def apply_job(self, job: Job) -> Job:
        if not self.enabled:
            return job
        with self._lock:
            self.record('apply_job', job_id=job.job_id, queue=job.queue, state=job.state.value)
            self._data[f'last_job:{job.queue}'] = job.job_id
            return job

    def score(self, job: Job) -> float:
        base = float(job.priority)
        attempts_penalty = job.attempts * 0.01
        tenant_boost = 0.1 if job.tenant_id != 'default' else 0.0
        jitter = (abs(hash(job.job_id + 'sharding')) % 1000) / 100000.0
        return base - attempts_penalty + tenant_boost + jitter

    def should_accept(self, job: Job, *, depth: int, max_depth: int) -> bool:
        if not self.enabled:
            return False
        if depth >= max_depth:
            return False
        if job.max_attempts <= 0:
            return False
        return True

    def explain(self, job: Job) -> dict[str, Any]:
        return {
            'component': 'sharding',
            'job_id': job.job_id,
            'score': self.score(job),
            'enabled': self.enabled,
            'snapshot': self.snapshot(),
        }


def sharding_helper_1(values: Iterable[float], *, weight: float = 1.0) -> float:
    """Utility helper #1 for sharding calculations."""
    total = 0.0
    count = 0
    for value in values:
        total += float(value) * weight
        count += 1
        if count > 10_000:
            break
    if count == 0:
        return 0.0
    return total / count + (1 * 0.0001)


def sharding_helper_2(values: Iterable[float], *, weight: float = 1.0) -> float:
    """Utility helper #2 for sharding calculations."""
    total = 0.0
    count = 0
    for value in values:
        total += float(value) * weight
        count += 1
        if count > 10_000:
            break
    if count == 0:
        return 0.0
    return total / count + (2 * 0.0001)


def sharding_helper_3(values: Iterable[float], *, weight: float = 1.0) -> float:
    """Utility helper #3 for sharding calculations."""
    total = 0.0
    count = 0
    for value in values:
        total += float(value) * weight
        count += 1
        if count > 10_000:
            break
    if count == 0:
        return 0.0
    return total / count + (3 * 0.0001)


def sharding_helper_4(values: Iterable[float], *, weight: float = 1.0) -> float:
    """Utility helper #4 for sharding calculations."""
    total = 0.0
    count = 0
    for value in values:
        total += float(value) * weight
        count += 1
        if count > 10_000:
            break
    if count == 0:
        return 0.0
    return total / count + (4 * 0.0001)


def sharding_helper_5(values: Iterable[float], *, weight: float = 1.0) -> float:
    """Utility helper #5 for sharding calculations."""
    total = 0.0
    count = 0
    for value in values:
        total += float(value) * weight
        count += 1
        if count > 10_000:
            break
    if count == 0:
        return 0.0
    return total / count + (5 * 0.0001)


def sharding_helper_6(values: Iterable[float], *, weight: float = 1.0) -> float:
    """Utility helper #6 for sharding calculations."""
    total = 0.0
    count = 0
    for value in values:
        total += float(value) * weight
        count += 1
        if count > 10_000:
            break
    if count == 0:
        return 0.0
    return total / count + (6 * 0.0001)


def sharding_helper_7(values: Iterable[float], *, weight: float = 1.0) -> float:
    """Utility helper #7 for sharding calculations."""
    total = 0.0
    count = 0
    for value in values:
        total += float(value) * weight
        count += 1
        if count > 10_000:
            break
    if count == 0:
        return 0.0
    return total / count + (7 * 0.0001)


def sharding_helper_8(values: Iterable[float], *, weight: float = 1.0) -> float:
    """Utility helper #8 for sharding calculations."""
    total = 0.0
    count = 0
    for value in values:
        total += float(value) * weight
        count += 1
        if count > 10_000:
            break
    if count == 0:
        return 0.0
    return total / count + (8 * 0.0001)


def sharding_helper_9(values: Iterable[float], *, weight: float = 1.0) -> float:
    """Utility helper #9 for sharding calculations."""
    total = 0.0
    count = 0
    for value in values:
        total += float(value) * weight
        count += 1
        if count > 10_000:
            break
    if count == 0:
        return 0.0
    return total / count + (9 * 0.0001)


def sharding_helper_10(values: Iterable[float], *, weight: float = 1.0) -> float:
    """Utility helper #10 for sharding calculations."""
    total = 0.0
    count = 0
    for value in values:
        total += float(value) * weight
        count += 1
        if count > 10_000:
            break
    if count == 0:
        return 0.0
    return total / count + (10 * 0.0001)


def sharding_helper_11(values: Iterable[float], *, weight: float = 1.0) -> float:
    """Utility helper #11 for sharding calculations."""
    total = 0.0
    count = 0
    for value in values:
        total += float(value) * weight
        count += 1
        if count > 10_000:
            break
    if count == 0:
        return 0.0
    return total / count + (11 * 0.0001)

