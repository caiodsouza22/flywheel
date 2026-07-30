"""Tests for load simulation."""

from __future__ import annotations

from datetime import datetime, timezone

from allot import (
    AllocationEngine,
    Budget,
    FrozenClock,
    InMemoryStore,
    Quota,
    Resource,
    Tenant,
)
from allot.simulation import (
    BurstPattern,
    ConstantRatePattern,
    LoadSimulator,
    MixedPattern,
    summarize_decisions,
    weighted_round_robin,
)


def test_constant_rate_simulation_denies_after_budget() -> None:
    store = InMemoryStore()
    store.seed(
        tenants=[Tenant(id="acme")],
        resources=[Resource(name="api", capacity=1000)],
        quotas=[Quota(tenant_id="acme", resource="api", limit=1000)],
        budgets=[Budget(tenant_id="acme", resource="api", allowance=10, window_seconds=3600)],
    )
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    clock = FrozenClock(start)
    engine = AllocationEngine(store, clock=clock)
    sim = LoadSimulator(engine=engine, clock=clock, start=start)
    report = sim.run(
        ConstantRatePattern(
            tenant_id="acme",
            resource="api",
            amount=5,
            every_seconds=1,
            count=4,
        )
    )
    assert report.granted_total == 10
    assert report.denied_count == 2


def test_mixed_pattern_and_round_robin() -> None:
    pattern = MixedPattern(
        patterns=[
            BurstPattern(tenant_id="a", resource="api", amount=1, burst_size=2),
            ConstantRatePattern(
                tenant_id="b",
                resource="api",
                amount=1,
                every_seconds=1,
                count=2,
            ),
        ]
    )
    points = list(pattern.generate())
    assert len(points) == 4
    rr = weighted_round_robin(
        [Tenant(id="a", weight=2), Tenant(id="b", weight=1)],
        resource="api",
        amount=1,
        ticks=3,
    )
    assert len(rr) == 3
    summary = summarize_decisions([])
    assert summary["granted_total"] == 0
