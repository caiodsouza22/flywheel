"""Tests for flywheel.tenure."""

from datetime import datetime, timedelta, timezone

from flywheel.tenure import TenureTracker


def test_tenure_age() -> None:
    tracker = TenureTracker()
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    tracker.mark_leased("j1", now=start)
    age = tracker.age_seconds("j1", now=start + timedelta(seconds=12))
    assert age == 12.0
    tracker.clear("j1")
    assert tracker.age_seconds("j1") is None