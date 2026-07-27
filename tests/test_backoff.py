"""Tests for exponential backoff."""

from __future__ import annotations

from allot.backoff import ExponentialBackoff


def test_backoff_sequence_caps() -> None:
    backoff = ExponentialBackoff(base_seconds=0.1, factor=2, max_seconds=0.5)
    delays = backoff.delays(5)
    assert delays[0] == 0.1
    assert delays[1] == 0.2
    assert delays[2] == 0.4
    assert delays[3] == 0.5
    assert delays[4] == 0.5
