"""Tests for allocation hooks."""

from __future__ import annotations

from allot import AllocationDecision, AllocationRequest, DecisionKind
from allot.hooks import CallableHook, HookChain, RecordingHook


def test_hook_chain_order() -> None:
    seen: list[str] = []

    def before(request: AllocationRequest) -> AllocationRequest:
        seen.append("before")
        return request

    def after(request: AllocationRequest, decision: AllocationDecision) -> None:
        seen.append("after")

    chain = HookChain()
    chain.add(CallableHook(before=before, after=after))
    recorder = RecordingHook()
    chain.add(recorder)
    request = AllocationRequest(tenant_id="acme", resource="api", amount=1)
    decision = AllocationDecision(
        kind=DecisionKind.GRANTED,
        tenant_id="acme",
        resource="api",
        requested=1,
        granted=1,
    )
    assert chain.before_allocate(request).amount == 1
    chain.after_allocate(request, decision)
    assert seen == ["before", "after"]
    assert len(recorder.decisions) == 1
