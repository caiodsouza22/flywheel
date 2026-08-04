"""Append-only JSONL journal for durable decision history."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Iterator

from allot.clock import Clock, SystemClock
from allot.models import AllocationDecision, AllocationRequest
from allot.serialization import decision_to_dict, request_to_dict


@dataclass(frozen=True, slots=True)
class JournalEntry:
    at: datetime
    request: dict
    decision: dict

    def to_line(self) -> str:
        return json.dumps(
            {
                "at": self.at.isoformat(),
                "request": self.request,
                "decision": self.decision,
            },
            sort_keys=True,
        )


class DecisionJournal:
    def __init__(self, path: str | Path, *, clock: Clock | None = None) -> None:
        self._path = Path(path)
        self._clock = clock or SystemClock()
        self._lock = RLock()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.touch()

    @property
    def path(self) -> Path:
        return self._path

    def append(self, request: AllocationRequest, decision: AllocationDecision) -> JournalEntry:
        entry = JournalEntry(
            at=self._clock.now(),
            request=request_to_dict(request),
            decision=decision_to_dict(decision),
        )
        with self._lock:
            with self._path.open("a", encoding="utf-8") as handle:
                handle.write(entry.to_line() + "\n")
        return entry

    def read(self) -> list[JournalEntry]:
        return list(self.iter_entries())

    def iter_entries(self) -> Iterator[JournalEntry]:
        with self._lock:
            text = self._path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            yield JournalEntry(
                at=datetime.fromisoformat(payload["at"]),
                request=payload["request"],
                decision=payload["decision"],
            )

    def count(self) -> int:
        return sum(1 for _ in self.iter_entries())

    def granted_total(self) -> float:
        total = 0.0
        for entry in self.iter_entries():
            total += float(entry.decision.get("granted", 0))
        return total
