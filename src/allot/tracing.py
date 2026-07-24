"""Lightweight in-process trace spans for allocation debugging."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import RLock
from typing import Any, Iterator
from contextlib import contextmanager

from allot.clock import Clock, SystemClock


@dataclass(frozen=True, slots=True)
class Span:
    name: str
    started_at: datetime
    ended_at: datetime | None
    attributes: dict[str, Any]

    @property
    def duration_seconds(self) -> float | None:
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()


@dataclass
class Tracer:
    _spans: list[Span] = field(default_factory=list)
    _lock: RLock = field(default_factory=RLock)
    _clock: Clock = field(default_factory=SystemClock)

    def set_clock(self, clock: Clock) -> None:
        self._clock = clock

    @contextmanager
    def span(self, name: str, **attributes: Any) -> Iterator[dict[str, Any]]:
        started = self._clock.now()
        attrs = dict(attributes)
        try:
            yield attrs
        finally:
            ended = self._clock.now()
            with self._lock:
                self._spans.append(
                    Span(
                        name=name,
                        started_at=started,
                        ended_at=ended,
                        attributes=attrs,
                    )
                )

    def spans(self) -> list[Span]:
        with self._lock:
            return list(self._spans)

    def clear(self) -> None:
        with self._lock:
            self._spans.clear()
