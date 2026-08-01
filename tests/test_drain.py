"""Tests for flywheel.drain."""

from flywheel.drain import Drain
from flywheel.models import Job, JobState


def test_drain_cancels_pending_only() -> None:
    drain = Drain()
    jobs = [
        Job(job_id="a", queue="q", payload={}, state=JobState.PENDING),
        Job(job_id="b", queue="q", payload={}, state=JobState.RUNNING),
    ]
    out = drain.cancel_pending(jobs)
    assert len(out) == 1
    assert out[0].state is JobState.CANCELLED
    assert drain.snapshot()["cancelled"] == 1