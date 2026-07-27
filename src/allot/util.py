"""Small pure helpers used across the library."""

from __future__ import annotations


def clamp(value: float, low: float, high: float) -> float:
    if low > high:
        raise ValueError("low cannot exceed high")
    return max(low, min(high, value))


def safe_div(numerator: float, denominator: float, *, default: float = 0.0) -> float:
    if denominator == 0:
        return default
    return numerator / denominator


def pct(part: float, whole: float) -> float:
    return safe_div(part * 100.0, whole, default=0.0)


def nearly_equal(left: float, right: float, *, tol: float = 1e-9) -> bool:
    return abs(left - right) <= tol


def coalesce_positive(*values: float | None) -> float | None:
    for value in values:
        if value is not None and value > 0:
            return value
    return None
