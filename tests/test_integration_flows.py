"""End-to-end integration flows across multiple allot subsystems."""

from __future__ import annotations

from datetime import datetime, timezone

from allot import (
    AllocationEngine,
    AllocationRequest,
    Budget,
    FrozenClock,
    InMemoryStore,
    Quota,
    Resource,
    Softness,
    Tenant,
)
from allot.alerts import AlertHub, ThresholdRule
from allot.denylist import AccessLists
from allot.engine_ext import EngineFacade
from allot.event_bus import EventBus, EventType, RecordingSubscriber
from allot.hooks import HookChain, RecordingHook
from allot.idempotency import IdempotencyStore
from allot.metrics import MetricsRegistry
from allot.report import build_system_report
from allot.simulation import ConstantRatePattern, LoadSimulator
from allot.tiering import default_saas_tiers
from allot.adapters.sqlite_store import SqliteStore


def test_facade_metrics_events_and_alerts_flow() -> None:
    store = InMemoryStore()
    store.put_resource(Resource(name="api_calls", capacity=10_000))
    catalog = default_saas_tiers()
    catalog.apply(store, "acme", "free")

    clock = FrozenClock(datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc))
    engine = AllocationEngine(store, clock=clock)
    hooks = HookChain()
    recorder = RecordingHook()
    hooks.add(recorder)
    access = AccessLists()
    access.allow_tenant("acme")
    facade = EngineFacade(
        engine=engine,
        hooks=hooks,
        access=access,
        idempotency=IdempotencyStore(ttl_seconds=60),
    )
    facade.idempotency.set_clock(clock)

    bus = EventBus()
    bus.set_clock(clock)
    subscriber = RecordingSubscriber()
    bus.subscribe(EventType.ALLOCATION, subscriber)
    bus.subscribe(EventType.DENIAL, subscriber)
    metrics = MetricsRegistry()
    hub = AlertHub()
    hub.set_clock(clock)

    decisions = []
    for index in range(5):
        request = AllocationRequest(tenant_id="acme", resource="api_calls", amount=30)
        decision = facade.allocate(request, idempotency_key=f"k-{index}")
        decisions.append(decision)
        bus.publish_decision(request, decision)
        metrics.observe_decision(decision)

    # Replay one key.
    replay = facade.allocate(
        AllocationRequest(tenant_id="acme", resource="api_calls", amount=30),
        idempotency_key="k-0",
    )
    assert replay == decisions[0]
    assert len(recorder.decisions) == 5
    assert len(subscriber.events) == 5
    assert metrics.snapshot()
    assert any(decision.granted > 0 for decision in decisions)

    report = build_system_report(store, decisions)
    assert report.usage_total > 0
    hub.check_usage_ratio(
        store,
        tenant_id="acme",
        resource="api_calls",
        limit=100,
        rules=[ThresholdRule(name="halfway", ratio=0.5)],
    )
    assert hub.history()


def test_sqlite_engine_simulation(tmp_path) -> None:
    store = SqliteStore(tmp_path / "sim.db")
    store.seed(
        tenants=[Tenant(id="acme"), Tenant(id="beta")],
        resources=[Resource(name="api", capacity=500)],
        quotas=[
            Quota(tenant_id="acme", resource="api", limit=200),
            Quota(tenant_id="beta", resource="api", limit=200, softness=Softness.HARD),
        ],
        budgets=[
            Budget(tenant_id="acme", resource="api", allowance=40, window_seconds=3600),
            Budget(tenant_id="beta", resource="api", allowance=40, window_seconds=3600),
        ],
    )
    start = datetime(2024, 2, 1, tzinfo=timezone.utc)
    clock = FrozenClock(start)
    engine = AllocationEngine(store, clock=clock)
    sim = LoadSimulator(engine=engine, clock=clock, start=start)
    report = sim.run(
        ConstantRatePattern(
            tenant_id="acme",
            resource="api",
            amount=10,
            every_seconds=1,
            count=6,
        )
    )
    assert report.granted_total == 40
    assert report.denied_count == 2
    store.close()
