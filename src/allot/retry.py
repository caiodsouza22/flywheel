"""Retry helpers for transient allocation denials."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from allot.models import AllocationDecision, AllocationRequest, DecisionKind


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    accept_partial: bool = False

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")


def allocate_with_retry(
    allocate: Callable[[AllocationRequest], AllocationDecision],
    request: AllocationRequest,
    policy: RetryPolicy | None = None,
) -> AllocationDecision:
    policy = policy or RetryPolicy()
    last: AllocationDecision | None = None
    for _ in range(policy.max_attempts):
        last = allocate(request)
        if last.kind is DecisionKind.GRANTED:
            return last
        if last.kind is DecisionKind.PARTIAL and policy.accept_partial:
            return last
    assert last is not None
    return last
