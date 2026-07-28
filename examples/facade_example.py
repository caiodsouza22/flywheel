"""Example: EngineFacade with idempotency and access lists."""

from __future__ import annotations

from allot import AllocationEngine, AllocationRequest, InMemoryStore, Resource, Tenant
from allot.denylist import AccessLists
from allot.engine_ext import EngineFacade
from allot.idempotency import IdempotencyStore


def main() -> None:
    store = InMemoryStore()
    store.seed(
        tenants=[Tenant(id="acme")],
        resources=[Resource(name="api", capacity=100)],
    )
    access = AccessLists()
    access.allow_tenant("acme")
    facade = EngineFacade(
        engine=AllocationEngine(store),
        access=access,
        idempotency=IdempotencyStore(ttl_seconds=300),
        validate=True,
    )
    request = AllocationRequest(tenant_id="acme", resource="api", amount=3)
    print(facade.allocate(request, idempotency_key="demo-1"))
    print(facade.allocate(request, idempotency_key="demo-1"))


if __name__ == "__main__":
    main()
