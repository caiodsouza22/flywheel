"""Tests for evaluation windows."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from allot import FixedWindow, InvalidWindow, SlidingWindow, WindowBounds


def test_fixed_window_alignment() -> None:
    window = FixedWindow(size_seconds=60)
    instant = datetime(2024, 1, 15, 12, 0, 30, tzinfo=timezone.utc)
    bounds = window.bounds_at(instant)
    assert bounds.start == datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    assert bounds.end == datetime(2024, 1, 15, 12, 1, 0, tzinfo=timezone.utc)
    assert bounds.contains(instant)
    assert not bounds.contains(bounds.end)


def test_sliding_window_trails_instant() -> None:
    window = SlidingWindow(size_seconds=30)
    instant = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    bounds = window.bounds_at(instant)
    assert bounds.duration_seconds == 30
    assert bounds.end == instant


def test_window_bounds_require_aware_datetimes() -> None:
    with pytest.raises(InvalidWindow):
        WindowBounds(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 2, tzinfo=timezone.utc),
        )


def test_fixed_window_rejects_naive_instant() -> None:
    window = FixedWindow(size_seconds=10)
    with pytest.raises(InvalidWindow):
        window.bounds_at(datetime(2024, 1, 1, 0, 0, 0))


def test_fixed_window_rejects_non_positive_size() -> None:
    with pytest.raises(InvalidWindow):
        FixedWindow(size_seconds=0)
