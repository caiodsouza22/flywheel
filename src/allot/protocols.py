"""Structural protocols for allot extension points."""

from __future__ import annotations

from typing import Protocol

from allot.models import AllocationDecision, AllocationRequest
from allot.store import Store


class SupportsAllocate(Protocol):
    def allocate(self, request: AllocationRequest) -> AllocationDecision: ...


class SupportsStore(Protocol):
    @property
    def store(self) -> Store: ...


class DecisionObserver(Protocol):
    def observe(self, request: AllocationRequest, decision: AllocationDecision) -> None: ...
