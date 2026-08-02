"""Tests for event bus."""

from __future__ import annotations

from allot import AllocationDecision, AllocationRequest, DecisionKind
from allot.event_bus import EventBus, EventType, RecordingSubscriber, on_event


def test_publish_decision_and_decorator() -> None:
    bus = EventBus()
    recorder = RecordingSubscriber()
    bus.subscribe(EventType.ALLOCATION, recorder)

    @on_event(bus, EventType.DENIAL)
    def on_denial(event) -> None:
        recorder(event)

    request = AllocationRequest(tenant_id="acme", resource="api", amount=1)
    granted = AllocationDecision(
        kind=DecisionKind.GRANTED,
        tenant_id="acme",
        resource="api",
        requested=1,
        granted=1,
    )
    denied = AllocationDecision(
        kind=DecisionKind.DENIED,
        tenant_id="acme",
        resource="api",
        requested=1,
        granted=0,
    )
    bus.publish_decision(request, granted)
    bus.publish_decision(request, denied)
    assert len(bus.history(EventType.ALLOCATION)) == 1
    assert len(bus.history(EventType.DENIAL)) == 1
    assert len(recorder.events) == 2
