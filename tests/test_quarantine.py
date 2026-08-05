"""Tests for flywheel.quarantine."""

from flywheel.quarantine import Quarantine


def test_quarantine_blocks_ids() -> None:
    q = Quarantine()
    q.add("bad1", note="oversized")
    assert q.blocked("bad1") is True
    assert q.blocked("ok") is False
    q.remove("bad1")
    assert q.blocked("bad1") is False