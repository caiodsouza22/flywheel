# flywheel

Python library for fair job queues, worker leases, retries, and dead-letter handling.

## Features

- Named queues with fairness and priority scoring
- Worker leases with fencing tokens
- Retry/backoff, circuit breaking, and DLQ
- Maintenance helpers: pause gate, drain, quarantine

## Develop

```bash
pip install -e ".[dev]"
pytest -q
```