"""Tests for util helpers."""

from __future__ import annotations

import pytest

from allot.util import clamp, coalesce_positive, nearly_equal, pct, safe_div


def test_util_helpers() -> None:
    assert clamp(5, 0, 3) == 3
    assert safe_div(1, 0) == 0
    assert pct(1, 4) == 25
    assert nearly_equal(0.1 + 0.2, 0.3)
    assert coalesce_positive(None, 0, 2) == 2
    with pytest.raises(ValueError):
        clamp(1, 5, 2)
