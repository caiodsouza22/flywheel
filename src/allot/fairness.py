"""Weighted fair queuing helpers for delayed allocation under contention."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from threading import RLock
from typing import Iterator

from allot.models import AllocationRequest, Tenant


@dataclass(order=True)
class _QueueItem:
    virtual_finish: float
    seq: int
    request: AllocationRequest = field(compare=False)
    weight: float = field(compare=False)


@dataclass
class FairQueue:
    """Min-heap fair queue ordered by virtual finish time.

    Tenants with higher weight advance virtual time more slowly, so they receive
    a larger long-run share when many requests wait.
    """

    _heap: list[_QueueItem] = field(default_factory=list)
    _seq: int = 0
    _virtual_time: float = 0.0
    _lock: RLock = field(default_factory=RLock)

    def __len__(self) -> int:
        with self._lock:
            return len(self._heap)

    def enqueue(self, request: AllocationRequest, tenant: Tenant) -> None:
        if tenant.id != request.tenant_id:
            raise ValueError("tenant id must match request.tenant_id")
        with self._lock:
            start = max(self._virtual_time, self._peek_start_locked())
            finish = start + (request.amount / tenant.weight)
            item = _QueueItem(
                virtual_finish=finish,
                seq=self._seq,
                request=request,
                weight=tenant.weight,
            )
            self._seq += 1
            heapq.heappush(self._heap, item)

    def dequeue(self) -> AllocationRequest:
        with self._lock:
            if not self._heap:
                raise IndexError("fair queue is empty")
            item = heapq.heappop(self._heap)
            self._virtual_time = max(self._virtual_time, item.virtual_finish)
            return item.request

    def peek(self) -> AllocationRequest | None:
        with self._lock:
            if not self._heap:
                return None
            return self._heap[0].request

    def drain(self, limit: int | None = None) -> list[AllocationRequest]:
        results: list[AllocationRequest] = []
        with self._lock:
            while self._heap and (limit is None or len(results) < limit):
                item = heapq.heappop(self._heap)
                self._virtual_time = max(self._virtual_time, item.virtual_finish)
                results.append(item.request)
        return results

    def __iter__(self) -> Iterator[AllocationRequest]:
        return iter(self.drain())

    def _peek_start_locked(self) -> float:
        if not self._heap:
            return self._virtual_time
        top = self._heap[0]
        return top.virtual_finish - (top.request.amount / top.weight)
