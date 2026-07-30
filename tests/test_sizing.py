"""Tests for quota sizing helpers."""

from __future__ import annotations

from allot.sizing import recommend_limit, utilization


def test_recommend_limit_with_headroom() -> None:
    hint = recommend_limit([10, 20, 30, 40, 50], percentile=1.0, headroom_ratio=0.1)
    assert hint.recommended_limit == 55
    assert hint.samples == 5
    assert utilization(50, 100) == 0.5
