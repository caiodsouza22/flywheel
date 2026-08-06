"""Minimal example sketch for enqueue + worker concepts."""

from flywheel.models import EnqueueRequest, Job, JobState


def main() -> None:
    req = EnqueueRequest(queue="default", payload={"hello": "world"})
    job = Job(job_id="demo", queue=req.queue, payload=req.payload, state=JobState.PENDING)
    print(job.job_id, job.state)


if __name__ == "__main__":
    main()
