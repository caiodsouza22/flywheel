"""Lightweight counters and snapshots for allocation observability."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any

from allot.models import AllocationDecision, DecisionKind


@dataclass
class Counter:
    name: str
    value: float = 0.0

    def inc(self, amount: float = 1.0) -> float:
        if amount < 0:
            raise ValueError("counter increment cannot be negative")
        self.value += amount
        return self.value


@dataclass
class MetricsRegistry:
    """Named counters grouped by optional label sets."""

    _counters: dict[tuple[str, tuple[tuple[str, str], ...]], Counter] = field(
        default_factory=dict
    )
    _lock: RLock = field(default_factory=RLock)

    def counter(self, name: str, **labels: str) -> Counter:
        key = (name, tuple(sorted(labels.items())))
        with self._lock:
            counter = self._counters.get(key)
            if counter is None:
                counter = Counter(name=name)
                self._counters[key] = counter
            return counter

    def observe_decision(self, decision: AllocationDecision) -> None:
        labels = {
            "tenant": decision.tenant_id,
            "resource": decision.resource,
            "kind": decision.kind.value,
        }
        self.counter("allot_allocations_total", **labels).inc()
        self.counter("allot_granted_amount", **labels).inc(decision.granted)
        if decision.kind is DecisionKind.DENIED:
            self.counter("allot_denials_total", tenant=decision.tenant_id).inc()

    def snapshot(self) -> list[dict[str, Any]]:
        with self._lock:
            rows: list[dict[str, Any]] = []
            for (name, labels), counter in sorted(self._counters.items()):
                rows.append(
                    {
                        "name": name,
                        "labels": dict(labels),
                        "value": counter.value,
                    }
                )
            return rows

    def render_prometheus(self) -> str:
        lines: list[str] = []
        for row in self.snapshot():
            labels = row["labels"]
            if labels:
                label_text = ",".join(
                    f'{key}="{value}"' for key, value in sorted(labels.items())
                )
                lines.append(f"{row['name']}{{{label_text}}} {row['value']}")
            else:
                lines.append(f"{row['name']} {row['value']}")
        return "\n".join(lines) + ("\n" if lines else "")

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
