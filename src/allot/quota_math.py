"""Pure math helpers for quota burn projections and replenishment."""

from __future__ import annotations

from dataclasses import dataclass

from allot.util import clamp, safe_div


@dataclass(frozen=True, slots=True)
class BurnProjection:
    remaining: float
    burn_per_second: float
    seconds_to_exhaustion: float | None
    exhausts: bool


def project_burn(
    *,
    remaining: float,
    burn_per_second: float,
) -> BurnProjection:
    if remaining < 0:
        raise ValueError("remaining cannot be negative")
    if burn_per_second < 0:
        raise ValueError("burn_per_second cannot be negative")
    if burn_per_second == 0:
        return BurnProjection(
            remaining=remaining,
            burn_per_second=0.0,
            seconds_to_exhaustion=None,
            exhausts=False,
        )
    seconds = remaining / burn_per_second
    return BurnProjection(
        remaining=remaining,
        burn_per_second=burn_per_second,
        seconds_to_exhaustion=seconds,
        exhausts=True,
    )


def replenish_amount(
    *,
    capacity: float,
    current: float,
    refill_per_second: float,
    elapsed_seconds: float,
) -> float:
    if capacity < 0 or current < 0 or refill_per_second < 0 or elapsed_seconds < 0:
        raise ValueError("inputs cannot be negative")
    refilled = current + refill_per_second * elapsed_seconds
    return clamp(refilled, 0.0, capacity)


def fair_share(total: float, weights: dict[str, float]) -> dict[str, float]:
    if total < 0:
        raise ValueError("total cannot be negative")
    if any(weight <= 0 for weight in weights.values()):
        raise ValueError("weights must be positive")
    weight_sum = sum(weights.values())
    if weight_sum <= 0:
        raise ValueError("weight_sum must be positive")
    return {
        key: total * safe_div(weight, weight_sum)
        for key, weight in sorted(weights.items())
    }


def utilization_band(ratio: float) -> str:
    ratio = clamp(ratio, 0.0, 1.0)
    if ratio < 0.5:
        return "low"
    if ratio < 0.8:
        return "medium"
    if ratio < 0.95:
        return "high"
    return "critical"


def ema(previous: float, sample: float, *, alpha: float) -> float:
    if not 0 < alpha <= 1:
        raise ValueError("alpha must be within (0, 1]")
    return alpha * sample + (1 - alpha) * previous
