"""Helpers for recommending quota/budget sizes from observed usage."""

from __future__ import annotations

from dataclasses import dataclass

from allot.util import clamp, safe_div


@dataclass(frozen=True, slots=True)
class SizingHint:
    recommended_limit: float
    headroom_ratio: float
    samples: int


def recommend_limit(
    samples: list[float],
    *,
    percentile: float = 0.95,
    headroom_ratio: float = 0.2,
) -> SizingHint:
    if not samples:
        raise ValueError("samples must be non-empty")
    if not 0 < percentile <= 1:
        raise ValueError("percentile must be within (0, 1]")
    if headroom_ratio < 0:
        raise ValueError("headroom_ratio cannot be negative")

    ordered = sorted(samples)
    index = int(round((len(ordered) - 1) * percentile))
    index = int(clamp(index, 0, len(ordered) - 1))
    baseline = ordered[index]
    recommended = baseline * (1.0 + headroom_ratio)
    return SizingHint(
        recommended_limit=recommended,
        headroom_ratio=headroom_ratio,
        samples=len(samples),
    )


def utilization(consumed: float, limit: float) -> float:
    return safe_div(consumed, limit, default=0.0)
