"""Tests for flywheel.seen."""

from flywheel.seen import SeenSet


def test_seen_set_capacity_and_hit() -> None:
    seen = SeenSet(capacity=2)
    assert seen.add("a") is True
    assert seen.add("a") is False
    assert seen.add("b") is True
    assert seen.add("c") is True
    assert seen.contains("a") is False
    assert seen.contains("c") is True