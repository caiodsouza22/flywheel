"""Shared fixtures for allot tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from allot import (
    AllocationEngine,
    Budget,
    FrozenClock,
    InMemoryStore,
    Quota,
    Resource,
    Softness,
    Tenant,
)


@pytest.fixture
def clock() -> FrozenClock:
    return FrozenClock(datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc))


@pytest.fixture
def store() -> InMemoryStore:
    memory = InMemoryStore()
    memory.seed(
        tenants=[
            Tenant(id="acme", weight=2.0),
            Tenant(id="beta", weight=1.0),
        ],
        resources=[
            Resource(name="api_calls", unit="call", capacity=1000.0),
            Resource(name="seats", unit="seat", capacity=50.0),
        ],
        quotas=[
            Quota(tenant_id="acme", resource="api_calls", limit=200.0),
            Quota(tenant_id="beta", resource="api_calls", limit=100.0, softness=Softness.SOFT),
        ],
        budgets=[
            Budget(
                tenant_id="acme",
                resource="api_calls",
                allowance=50.0,
                window_seconds=60,
            ),
        ],
    )
    return memory


@pytest.fixture
def engine(store: InMemoryStore, clock: FrozenClock) -> AllocationEngine:
    return AllocationEngine(store, clock=clock)
