"""Tests for flywheel.pause."""

from flywheel.pause import PauseGate


def test_pause_gate_blocks_claims() -> None:
    gate = PauseGate()
    assert gate.allow_claim() is True
    gate.close("deploy")
    assert gate.allow_claim() is False
    assert gate.snapshot()["reason"] == "deploy"
    gate.open()
    assert gate.allow_claim() is True