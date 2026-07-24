"""Tests for tracer spans."""

from __future__ import annotations

from datetime import datetime, timezone

from allot import FrozenClock
from allot.tracing import Tracer


def test_span_records_duration() -> None:
    clock = FrozenClock(datetime(2024, 1, 1, tzinfo=timezone.utc))
    tracer = Tracer()
    tracer.set_clock(clock)
    with tracer.span("allocate", tenant="acme") as attrs:
        attrs["granted"] = 1
        clock.advance(2)
    spans = tracer.spans()
    assert len(spans) == 1
    assert spans[0].duration_seconds == 2
    assert spans[0].attributes["granted"] == 1
