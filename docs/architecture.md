# Architecture

`allot` is organized around a small set of durable concepts:

1. **Registry state** — tenants, resources, quotas, and budgets live in a `Store`.
2. **Usage ledger** — consumed amounts are keyed by tenant, resource, and window.
3. **Policy** — pure decision logic that maps remaining capacity to a grant.
4. **Engine** — loads registry + usage, asks a policy, then commits usage.
5. **Facades** — optional layers for hooks, access lists, idempotency, and metrics.

## Extension points

- Implement `Store` for durable backends.
- Implement `Policy` for custom contention behavior.
- Wrap `AllocationEngine` with `EngineFacade` for service integration.
- Observe decisions through `AuditLog`, `MetricsRegistry`, or `Tracer`.

## Determinism

Clocks are injectable (`FrozenClock`) so window math and lease expiry can be
tested without sleeping. Rate limiters and backoff helpers avoid wall-clock
randomness unless explicitly configured.
