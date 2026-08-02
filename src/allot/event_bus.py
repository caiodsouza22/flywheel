"""In-process pub/sub bus for allocation lifecycle events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import RLock
from typing import Any, Callable, Protocol

from allot.clock import Clock, SystemClock
from allot.models import AllocationDecision, AllocationRequest


class EventType(str, Enum):
    ALLOCATION = "allocation"
    DENIAL = "denial"
    LEASE = "lease"
    RESERVATION = "reservation"
    CUSTOM = "custom"


@dataclass(frozen=True, slots=True)
class Event:
    type: EventType
    name: str
    at: datetime
    payload: dict[str, Any] = field(default_factory=dict)


class EventHandler(Protocol):
    def __call__(self, event: Event) -> None: ...


@dataclass
class EventBus:
    _subscribers: dict[EventType, list[EventHandler]] = field(default_factory=dict)
    _history: list[Event] = field(default_factory=list)
    _lock: RLock = field(default_factory=RLock)
    _clock: Clock = field(default_factory=SystemClock)
    history_limit: int = 1000

    def set_clock(self, clock: Clock) -> None:
        self._clock = clock

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        with self._lock:
            self._subscribers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        with self._lock:
            handlers = self._subscribers.get(event_type, [])
            self._subscribers[event_type] = [item for item in handlers if item is not handler]

    def publish(self, event_type: EventType, name: str, **payload: Any) -> Event:
        event = Event(
            type=event_type,
            name=name,
            at=self._clock.now(),
            payload=dict(payload),
        )
        with self._lock:
            self._history.append(event)
            if len(self._history) > self.history_limit:
                self._history = self._history[-self.history_limit :]
            handlers = list(self._subscribers.get(event_type, []))
            wildcard = list(self._subscribers.get(EventType.CUSTOM, []))
        for handler in handlers:
            handler(event)
        # CUSTOM subscribers receive everything when listening as catch-all only if subscribed to CUSTOM
        # Keep semantics strict: only matching type.
        _ = wildcard
        return event

    def publish_decision(self, request: AllocationRequest, decision: AllocationDecision) -> Event:
        event_type = EventType.DENIAL if decision.granted <= 0 else EventType.ALLOCATION
        return self.publish(
            event_type,
            "allocation_decision",
            tenant_id=request.tenant_id,
            resource=request.resource,
            requested=request.amount,
            granted=decision.granted,
            kind=decision.kind.value,
            reason=decision.reason,
        )

    def history(self, event_type: EventType | None = None) -> list[Event]:
        with self._lock:
            if event_type is None:
                return list(self._history)
            return [event for event in self._history if event.type is event_type]


@dataclass
class RecordingSubscriber:
    events: list[Event] = field(default_factory=list)

    def __call__(self, event: Event) -> None:
        self.events.append(event)


def on_event(bus: EventBus, event_type: EventType) -> Callable[[EventHandler], EventHandler]:
    def decorator(handler: EventHandler) -> EventHandler:
        bus.subscribe(event_type, handler)
        return handler

    return decorator
