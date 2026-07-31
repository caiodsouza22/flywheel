"""Shard routing for multi-partition capacity pools."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from threading import RLock
from typing import Iterable

from allot.errors import AllotError
from allot.models import AllocationRequest


class ShardError(AllotError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class Shard:
    id: str
    weight: float = 1.0
    labels: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("shard id must be non-empty")
        if self.weight <= 0:
            raise ValueError("shard weight must be positive")


@dataclass(frozen=True, slots=True)
class ShardAssignment:
    request: AllocationRequest
    shard: Shard
    key: str


class ShardRouter:
    def __init__(self, shards: Iterable[Shard] | None = None) -> None:
        self._shards: dict[str, Shard] = {}
        self._lock = RLock()
        for shard in shards or ():
            self.add(shard)

    def add(self, shard: Shard) -> None:
        with self._lock:
            if shard.id in self._shards:
                raise ShardError(f"duplicate shard id: {shard.id}")
            self._shards[shard.id] = shard

    def remove(self, shard_id: str) -> None:
        with self._lock:
            if shard_id not in self._shards:
                raise ShardError(f"unknown shard: {shard_id}")
            del self._shards[shard_id]

    def list_shards(self) -> list[Shard]:
        with self._lock:
            return sorted(self._shards.values(), key=lambda shard: shard.id)

    def route_key(self, request: AllocationRequest) -> str:
        explicit = request.metadata.get("shard_key")
        if explicit:
            return explicit
        return f"{request.tenant_id}:{request.resource}"

    def assign(self, request: AllocationRequest) -> ShardAssignment:
        with self._lock:
            if not self._shards:
                raise ShardError("no shards configured")
            key = self.route_key(request)
            shard = self._pick_locked(key)
            return ShardAssignment(request=request, shard=shard, key=key)

    def assign_many(self, requests: list[AllocationRequest]) -> list[ShardAssignment]:
        return [self.assign(request) for request in requests]

    def distribution(self, keys: list[str]) -> dict[str, int]:
        counts = {shard_id: 0 for shard_id in self._shards}
        with self._lock:
            for key in keys:
                shard = self._pick_locked(key)
                counts[shard.id] += 1
        return counts

    def _pick_locked(self, key: str) -> Shard:
        scored: list[tuple[float, Shard]] = []
        for shard in self._shards.values():
            digest = hashlib.sha256(f"{key}:{shard.id}".encode("utf-8")).hexdigest()
            unit = int(digest[:8], 16) / 0xFFFFFFFF
            score = unit / shard.weight
            scored.append((score, shard))
        scored.sort(key=lambda item: (item[0], item[1].id))
        return scored[0][1]


class ShardCapacityPlan:
    def __init__(self, router: ShardRouter) -> None:
        self._router = router

    def split(self, total_capacity: float) -> dict[str, float]:
        if total_capacity < 0:
            raise ValueError("total_capacity cannot be negative")
        shards = self._router.list_shards()
        if not shards:
            return {}
        weight_sum = sum(shard.weight for shard in shards)
        return {
            shard.id: total_capacity * (shard.weight / weight_sum)
            for shard in shards
        }
