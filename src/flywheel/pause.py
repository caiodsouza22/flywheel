"""Pause gate for temporarily stopping dequeue."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any


@dataclass
class PauseGate:
    """When closed, workers should stop claiming new work."""

    name: str = "pause"
    closed: bool = False
    _lock: RLock = field(default_factory=RLock, repr=False)
    _reason: str = ""

    def close(self, reason: str = "maintenance") -> None:
        with self._lock:
            self.closed = True
            self._reason = reason

    def open(self) -> None:
        with self._lock:
            self.closed = False
            self._reason = ""

    def allow_claim(self) -> bool:
        with self._lock:
            return not self.closed

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {"name": self.name, "closed": self.closed, "reason": self._reason}