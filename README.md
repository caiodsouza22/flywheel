# allot

Python library for **multi-tenant quota, budget, and rate allocation**.

Services that share capacity across tenants need more than a single counter:
rolling windows, burst headroom, fairness when demand exceeds supply, and
deterministic decisions that can be audited later. `allot` models that
problem as first-class types and an allocation engine with swappable stores.

## Status

Early development. Public APIs may change before 1.0.

## Install (editable)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## Design sketch

- **Quota** — hard or soft ceiling on a named resource for a tenant
- **Budget** — spendable allowance over a window (tokens, dollars, seats)
- **Window** — fixed, sliding, or calendar-aligned evaluation periods
- **Policy** — how contention is resolved (strict, burst, weighted fair)
- **Store** — persistence of counters and leases (memory first; others later)
- **Engine** — evaluate a request and return grant / deny / partial

## License

MIT
