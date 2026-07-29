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

## Quick start

```python
from allot import (
    AllocationEngine,
    AllocationRequest,
    InMemoryStore,
    Quota,
    Resource,
    Tenant,
)

store = InMemoryStore()
store.seed(
    tenants=[Tenant(id="acme")],
    resources=[Resource(name="api_calls", capacity=1000)],
    quotas=[Quota(tenant_id="acme", resource="api_calls", limit=100)],
)
decision = AllocationEngine(store).allocate(
    AllocationRequest(tenant_id="acme", resource="api_calls", amount=5)
)
print(decision.kind, decision.granted)
```

## CLI

```bash
allot show-config examples/sample_config.json
allot allocate examples/sample_config.json --tenant acme --resource api_calls --amount 5
```

## Design sketch

- **Quota** — hard or soft ceiling on a named resource for a tenant
- **Budget** — spendable allowance over a window (tokens, dollars, seats)
- **Window** — fixed, sliding, or calendar-aligned evaluation periods
- **Policy** — strict, burst, weighted fair, overdraft, composites
- **Store** — in-memory registry plus usage ledger; read-only adapter available
- **Engine** — evaluate a request and return grant / deny / partial
- **Leases / reservations** — fencing tokens and temporary holds
- **Facade** — hooks, denylist/allowlist, idempotency keys

## License

MIT
