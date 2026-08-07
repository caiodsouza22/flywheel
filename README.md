# flywheel

Python library for **fair job queues, worker leases, retries, and dead-letter handling**.

Background workers that share capacity across tenants need more than a FIFO
list: priority when the queue is hot, leases so two workers do not steal the
same job, retries with backoff when a handler flakes, and a dead-letter path
when attempts are exhausted. `flywheel` models that problem as first-class
types — jobs, queues, leases, receipts — plus helpers for fairness, pause /
drain maintenance, and quarantine.

## Status

Early development. Public APIs may change before 1.0.

## Install (editable)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

Imports resolve from `src/` (`PYTHONPATH=src` in the AfterQuery image).

## Quick start

```python
from flywheel import EnqueueRequest, Job, JobState, QueueSpec
from flywheel.priority import Priority
from flywheel.pause import PauseGate

spec = QueueSpec(name="default", max_depth=10_000, visibility_timeout_seconds=30.0)
req = EnqueueRequest(
    queue=spec.name,
    payload={"task": "resize", "id": 42},
    tenant_id="acme",
    priority=2.0,
    max_attempts=5,
)
job = Job(
    job_id="job_demo",
    queue=req.queue,
    payload=dict(req.payload),
    tenant_id=req.tenant_id,
    priority=float(req.priority or 0.0),
    state=JobState.PENDING,
    max_attempts=req.max_attempts,
)

gate = PauseGate()
priority = Priority()
print(gate.allow_claim(), priority.score(job), job.state.value)
```

See `examples/basic_enqueue.py`, `examples/facade_example.py`, and
`examples/sample_config.json` for more sketches.

## Design sketch

- **Job / EnqueueRequest** — work unit, payload, tenant, priority, attempts
- **QueueSpec** — named queue depth, visibility timeout, fairness flag
- **Lease** — worker claim with expiry and fencing token
- **Priority / Fairness** — score and share work across tenants
- **Backoff / Retry / Circuit** — re-queue timing and downstream protection
- **Dispatcher / Worker / Executor** — claim, run, ack or fail
- **Scheduler / Parking** — delayed availability and resume
- **DLQ** — terminal failures after retries are exhausted
- **Pause / Drain / Quarantine / SeenSet** — maintenance and safety helpers
- **Adapters** — memory, sqlite, file, and read-only store facades

## AfterQuery environment

Dependency image recipe lives in `environment/Dockerfile` (no `COPY`, pinned
pip deps, `PYTHONPATH=/app/src`). Publish steps are in `ENVIRONMENT.md`.

## License

MIT
