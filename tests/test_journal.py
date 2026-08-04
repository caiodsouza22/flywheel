"""Tests for decision journal."""

from __future__ import annotations

from datetime import datetime, timezone

from allot import AllocationDecision, AllocationRequest, DecisionKind, FrozenClock
from allot.journal import DecisionJournal


def test_journal_append_and_read(tmp_path) -> None:
    clock = FrozenClock(datetime(2024, 1, 1, tzinfo=timezone.utc))
    journal = DecisionJournal(tmp_path / "decisions.jsonl", clock=clock)
    request = AllocationRequest(tenant_id="acme", resource="api", amount=2)
    decision = AllocationDecision(
        kind=DecisionKind.GRANTED,
        tenant_id="acme",
        resource="api",
        requested=2,
        granted=2,
    )
    journal.append(request, decision)
    clock.advance(1)
    journal.append(request, decision)
    assert journal.count() == 2
    assert journal.granted_total() == 4
    entries = journal.read()
    assert entries[0].request["tenant_id"] == "acme"
