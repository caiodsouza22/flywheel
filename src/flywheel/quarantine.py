"""Quarantine list for suspicious job payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any


@dataclass
class Quarantine:
    """Holds job ids that should not be claimed until reviewed."""

    name: str = "quarantine"
    _lock: RLock = field(default_factory=RLock, repr=False)
    _ids: set[str] = field(default_factory=set, repr=False)
    _notes: dict[str, str] = field(default_factory=dict, repr=False)

    def add(self, job_id: str, note: str = "") -> None:
        with self._lock:
            self._ids.add(job_id)
            if note:
                self._notes[job_id] = note

    def remove(self, job_id: str) -> None:
        with self._lock:
            self._ids.discard(job_id)
            self._notes.pop(job_id, None)

    def blocked(self, job_id: str) -> bool:
        with self._lock:
            return job_id in self._ids

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {"name": self.name, "count": len(self._ids)}