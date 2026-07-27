"""AllocationEngine wrapper with hooks, denylist, and idempotency."""

from __future__ import annotations

from dataclasses import dataclass

from allot.denylist import AccessLists
from allot.engine import AllocationEngine
from allot.hooks import HookChain
from allot.idempotency import IdempotencyStore
from allot.models import AllocationDecision, AllocationRequest
from allot.validation import validate_request


@dataclass
class EngineFacade:
    """Higher-level allocate path used by services."""

    engine: AllocationEngine
    hooks: HookChain | None = None
    access: AccessLists | None = None
    idempotency: IdempotencyStore | None = None
    validate: bool = True

    def allocate(
        self,
        request: AllocationRequest,
        *,
        idempotency_key: str | None = None,
    ) -> AllocationDecision:
        if self.validate:
            validate_request(request, self.engine.store)
        if self.access is not None:
            self.access.check(request)
        if idempotency_key and self.idempotency is not None:
            replay = self.idempotency.replay_or_none(idempotency_key, request)
            if replay is not None:
                return replay

        working = request
        if self.hooks is not None:
            working = self.hooks.before_allocate(working)

        decision = self.engine.allocate(working)

        if self.hooks is not None:
            self.hooks.after_allocate(working, decision)
        if idempotency_key and self.idempotency is not None:
            self.idempotency.remember(idempotency_key, request, decision)
        return decision
