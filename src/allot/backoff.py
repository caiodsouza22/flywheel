"""Deterministic backoff sequences for retry loops."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExponentialBackoff:
    base_seconds: float = 0.05
    factor: float = 2.0
    max_seconds: float = 2.0
    jitter_ratio: float = 0.0

    def __post_init__(self) -> None:
        if self.base_seconds < 0:
            raise ValueError("base_seconds cannot be negative")
        if self.factor < 1:
            raise ValueError("factor must be >= 1")
        if self.max_seconds < self.base_seconds:
            raise ValueError("max_seconds must be >= base_seconds")
        if not 0 <= self.jitter_ratio <= 1:
            raise ValueError("jitter_ratio must be within [0, 1]")

    def delay_for_attempt(self, attempt: int) -> float:
        if attempt < 1:
            raise ValueError("attempt must be >= 1")
        delay = min(self.max_seconds, self.base_seconds * (self.factor ** (attempt - 1)))
        # Deterministic pseudo-jitter from attempt number (no randomness).
        if self.jitter_ratio:
            jitter = delay * self.jitter_ratio * ((attempt % 5) / 5.0)
            delay = min(self.max_seconds, delay + jitter)
        return delay

    def delays(self, attempts: int) -> list[float]:
        return [self.delay_for_attempt(i) for i in range(1, attempts + 1)]
