"""Example: seed a store and allocate once."""

from __future__ import annotations

from allot import (
    AllocationEngine,
    AllocationRequest,
    Budget,
    InMemoryStore,
    Quota,
    Resource,
    Tenant,
)


def main() -> None:
    store = InMemoryStore()
    store.seed(
        tenants=[Tenant(id="acme", weight=2.0)],
        resources=[Resource(name="api_calls", capacity=1000)],
        quotas=[Quota(tenant_id="acme", resource="api_calls", limit=100)],
        budgets=[
            Budget(
                tenant_id="acme",
                resource="api_calls",
                allowance=25,
                window_seconds=60,
            )
        ],
    )
    engine = AllocationEngine(store)
    decision = engine.allocate(
        AllocationRequest(tenant_id="acme", resource="api_calls", amount=10)
    )
    print(decision)


if __name__ == "__main__":
    main()
