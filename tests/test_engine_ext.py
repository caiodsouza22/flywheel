"""Tests for EngineFacade."""

from __future__ import annotations

from allot import AllocationEngine, AllocationRequest, DecisionKind
from allot.denylist import AccessLists
from allot.engine_ext import EngineFacade
from allot.hooks import RecordingHook, HookChain
from allot.idempotency import IdempotencyStore


def test_facade_idempotent_allocate(engine: AllocationEngine) -> None:
    hooks = HookChain()
    recorder = RecordingHook()
    hooks.add(recorder)
    facade = EngineFacade(
        engine=engine,
        hooks=hooks,
        access=AccessLists(),
        idempotency=IdempotencyStore(ttl_seconds=60),
    )
    request = AllocationRequest(tenant_id="acme", resource="api_calls", amount=3)
    first = facade.allocate(request, idempotency_key="req-1")
    second = facade.allocate(request, idempotency_key="req-1")
    assert first == second
    assert first.kind is DecisionKind.GRANTED
    assert len(recorder.decisions) == 1
