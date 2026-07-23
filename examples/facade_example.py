"""Facade-style sketch: enqueue concepts without a live worker loop."""

from __future__ import annotations

from flywheel.models import EnqueueRequest, Job, JobState
from flywheel.pause import PauseGate
from flywheel.priority import Priority


def main() -> None:
    gate = PauseGate()
    priority = Priority()
    req = EnqueueRequest(queue="default", payload={"task": "ping"}, tenant_id="acme", priority=1.5)
    job = Job(
        job_id="job_demo",
        queue=req.queue,
        payload=dict(req.payload),
        tenant_id=req.tenant_id,
        priority=float(req.priority or 0.0),
        state=JobState.PENDING,
    )
    print("claim_allowed", gate.allow_claim())
    print("score", priority.score(job))
    print("job", job.job_id, job.state.value)


if __name__ == "__main__":
    main()