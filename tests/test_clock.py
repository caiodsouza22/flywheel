"""Tests for flywheel.clock."""

from __future__ import annotations

from datetime import datetime, timezone

from flywheel.clock import Clock
from flywheel.models import Job, JobState


def test_clock_snapshot_and_score() -> None:
    comp = Clock(name="clock")
    job = Job(
        job_id="j1",
        queue="default",
        payload={"n": 1},
        tenant_id="acme",
        priority=2.0,
        state=JobState.PENDING,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    out = comp.apply_job(job)
    assert out.job_id == "j1"
    assert comp.score(job) >= 0.0
    snap = comp.snapshot()
    assert snap["name"] == "clock"
    assert snap["enabled"] is True
    assert comp.should_accept(job, depth=0, max_depth=100) is True
    assert comp.explain(job)["component"] == "clock"


def test_clock_incr_and_history() -> None:
    comp = Clock()
    assert comp.incr("hits", 2) == 2.0
    assert comp.get("hits") == 2.0
    comp.set("mode", "fast")
    assert comp.get("mode") == "fast"
    hist = comp.history(limit=10)
    assert isinstance(hist, list)
    comp.reset()
    assert comp.history() == []
