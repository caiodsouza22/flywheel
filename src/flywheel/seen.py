"""Bounded seen-set for recent job identifiers."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from threading import RLock
from typing import Any


@dataclass
class SeenSet:
    """Remember recent ids with a fixed capacity."""

    name: str = "seen"
    capacity: int = 10_000
    _lock: RLock = field(default_factory=RLock, repr=False)
    _items: OrderedDict[str, bool] = field(default_factory=OrderedDict, repr=False)

    def add(self, job_id: str) -> bool:
        """Return True if newly added, False if already present."""
        with self._lock:
            if job_id in self._items:
                self._items.move_to_end(job_id)
                return False
            self._items[job_id] = True
            while len(self._items) > self.capacity:
                self._items.popitem(last=False)
            return True

    def contains(self, job_id: str) -> bool:
        with self._lock:
            return job_id in self._items

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {"name": self.name, "size": len(self._items), "capacity": self.capacity}