"""Lifecycle hooks around allocation decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol

from allot.models import AllocationDecision, AllocationRequest


class AllocationHook(Protocol):
    def before_allocate(self, request: AllocationRequest) -> AllocationRequest: ...

    def after_allocate(
        self,
        request: AllocationRequest,
        decision: AllocationDecision,
    ) -> None: ...


@dataclass
class HookChain:
    """Runs hooks in registration order."""

    _hooks: list[AllocationHook] = field(default_factory=list)

    def add(self, hook: AllocationHook) -> None:
        self._hooks.append(hook)

    def before_allocate(self, request: AllocationRequest) -> AllocationRequest:
        current = request
        for hook in self._hooks:
            current = hook.before_allocate(current)
        return current

    def after_allocate(
        self,
        request: AllocationRequest,
        decision: AllocationDecision,
    ) -> None:
        for hook in self._hooks:
            hook.after_allocate(request, decision)


@dataclass
class CallableHook:
    """Adapter from plain callables to the hook protocol."""

    before: Callable[[AllocationRequest], AllocationRequest] | None = None
    after: Callable[[AllocationRequest, AllocationDecision], None] | None = None

    def before_allocate(self, request: AllocationRequest) -> AllocationRequest:
        if self.before is None:
            return request
        return self.before(request)

    def after_allocate(
        self,
        request: AllocationRequest,
        decision: AllocationDecision,
    ) -> None:
        if self.after is not None:
            self.after(request, decision)


@dataclass
class RecordingHook:
    """Test-friendly hook that records seen requests and decisions."""

    requests: list[AllocationRequest] = field(default_factory=list)
    decisions: list[AllocationDecision] = field(default_factory=list)

    def before_allocate(self, request: AllocationRequest) -> AllocationRequest:
        self.requests.append(request)
        return request

    def after_allocate(
        self,
        request: AllocationRequest,
        decision: AllocationDecision,
    ) -> None:
        self.decisions.append(decision)
