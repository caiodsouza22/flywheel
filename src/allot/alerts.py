"""Threshold alerts based on usage ratios and denial rates."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import RLock
from typing import Callable

from allot.clock import Clock, SystemClock
from allot.models import AllocationDecision, DecisionKind
from allot.store import Store, UsageKey


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class Alert:
    name: str
    severity: AlertSeverity
    message: str
    at: datetime
    labels: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ThresholdRule:
    name: str
    ratio: float
    severity: AlertSeverity = AlertSeverity.WARNING

    def __post_init__(self) -> None:
        if not 0 < self.ratio <= 1:
            raise ValueError("ratio must be within (0, 1]")


AlertHandler = Callable[[Alert], None]


@dataclass
class AlertHub:
    _handlers: list[AlertHandler] = field(default_factory=list)
    _history: list[Alert] = field(default_factory=list)
    _lock: RLock = field(default_factory=RLock)
    _clock: Clock = field(default_factory=SystemClock)

    def set_clock(self, clock: Clock) -> None:
        self._clock = clock

    def add_handler(self, handler: AlertHandler) -> None:
        with self._lock:
            self._handlers.append(handler)

    def emit(self, alert: Alert) -> None:
        with self._lock:
            self._history.append(alert)
            handlers = list(self._handlers)
        for handler in handlers:
            handler(alert)

    def history(self) -> list[Alert]:
        with self._lock:
            return list(self._history)

    def clear(self) -> None:
        with self._lock:
            self._history.clear()

    def check_usage_ratio(
        self,
        store: Store,
        *,
        tenant_id: str,
        resource: str,
        limit: float,
        rules: list[ThresholdRule],
        window_start_iso: str = "lifetime",
    ) -> list[Alert]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        consumed = store.get_usage(UsageKey(tenant_id, resource, window_start_iso))
        ratio = consumed / limit
        alerts: list[Alert] = []
        for rule in sorted(rules, key=lambda item: item.ratio):
            if ratio >= rule.ratio:
                alert = Alert(
                    name=rule.name,
                    severity=rule.severity,
                    message=(
                        f"usage ratio {ratio:.2%} for {tenant_id}/{resource} "
                        f"exceeded threshold {rule.ratio:.2%}"
                    ),
                    at=self._clock.now(),
                    labels={
                        "tenant": tenant_id,
                        "resource": resource,
                        "ratio": f"{ratio:.4f}",
                    },
                )
                self.emit(alert)
                alerts.append(alert)
        return alerts

    def check_denial_rate(
        self,
        decisions: list[AllocationDecision],
        *,
        threshold: float,
        name: str = "denial_rate",
        severity: AlertSeverity = AlertSeverity.CRITICAL,
    ) -> Alert | None:
        if not 0 < threshold <= 1:
            raise ValueError("threshold must be within (0, 1]")
        if not decisions:
            return None
        denied = sum(1 for item in decisions if item.kind is DecisionKind.DENIED)
        rate = denied / len(decisions)
        if rate < threshold:
            return None
        alert = Alert(
            name=name,
            severity=severity,
            message=f"denial rate {rate:.2%} exceeded threshold {threshold:.2%}",
            at=self._clock.now(),
            labels={"denial_rate": f"{rate:.4f}", "samples": str(len(decisions))},
        )
        self.emit(alert)
        return alert


class CollectingHandler:
    def __init__(self) -> None:
        self.alerts: list[Alert] = []

    def __call__(self, alert: Alert) -> None:
        self.alerts.append(alert)
