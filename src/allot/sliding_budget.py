"""Sliding-window budget accounting based on timestamped spend events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import RLock

from allot.clock import Clock, SystemClock
from allot.errors import InsufficientSlidingBudget, InvalidWindow
from allot.models import Softness


@dataclass(frozen=True, slots=True)
class SpendEvent:
    at: datetime
    amount: float
    tenant_id: str
    resource: str

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError("spend amount must be positive")
        if self.at.tzinfo is None:
            raise InvalidWindow("spend event timestamp must be timezone-aware")


@dataclass
class SlidingBudgetAccount:
    """Tracks spend events and evaluates remaining allowance in a trailing window."""

    tenant_id: str
    resource: str
    allowance: float
    window_seconds: int
    softness: Softness = Softness.HARD
    _events: list[SpendEvent] = field(default_factory=list)
    _lock: RLock = field(default_factory=RLock)

    def __post_init__(self) -> None:
        if self.allowance < 0:
            raise ValueError("allowance cannot be negative")
        if self.window_seconds <= 0:
            raise InvalidWindow("window_seconds must be positive")

    def spent_in_window(self, now: datetime) -> float:
        with self._lock:
            self._prune_locked(now)
            return sum(event.amount for event in self._events)

    def remaining(self, now: datetime) -> float:
        return max(0.0, self.allowance - self.spent_in_window(now))

    def can_spend(self, amount: float, now: datetime) -> bool:
        if amount <= 0:
            raise ValueError("amount must be positive")
        remaining = self.remaining(now)
        if remaining >= amount:
            return True
        return self.softness is Softness.SOFT

    def spend(self, amount: float, now: datetime) -> SpendEvent:
        if amount <= 0:
            raise ValueError("amount must be positive")
        with self._lock:
            self._prune_locked(now)
            spent = sum(event.amount for event in self._events)
            remaining = max(0.0, self.allowance - spent)
            if remaining < amount and self.softness is Softness.HARD:
                raise InsufficientSlidingBudget(
                    self.tenant_id,
                    self.resource,
                    amount,
                    remaining,
                )
            event = SpendEvent(
                at=now,
                amount=amount,
                tenant_id=self.tenant_id,
                resource=self.resource,
            )
            self._events.append(event)
            return event

    def events(self) -> list[SpendEvent]:
        with self._lock:
            return list(self._events)

    def _prune_locked(self, now: datetime) -> None:
        if now.tzinfo is None:
            raise InvalidWindow("now must be timezone-aware")
        cutoff = now - timedelta(seconds=self.window_seconds)
        self._events = [event for event in self._events if event.at >= cutoff]


class SlidingBudgetLedger:
    """Registry of sliding budget accounts keyed by tenant+resource."""

    def __init__(self, *, clock: Clock | None = None) -> None:
        self._clock = clock or SystemClock()
        self._accounts: dict[tuple[str, str], SlidingBudgetAccount] = {}
        self._lock = RLock()

    def register(self, account: SlidingBudgetAccount) -> None:
        with self._lock:
            self._accounts[(account.tenant_id, account.resource)] = account

    def get(self, tenant_id: str, resource: str) -> SlidingBudgetAccount:
        with self._lock:
            try:
                return self._accounts[(tenant_id, resource)]
            except KeyError as exc:
                raise KeyError(f"no sliding budget for {tenant_id}/{resource}") from exc

    def spend(self, tenant_id: str, resource: str, amount: float) -> SpendEvent:
        account = self.get(tenant_id, resource)
        return account.spend(amount, self._clock.now())

    def remaining(self, tenant_id: str, resource: str) -> float:
        account = self.get(tenant_id, resource)
        return account.remaining(self._clock.now())

    def accounts(self) -> list[SlidingBudgetAccount]:
        with self._lock:
            return sorted(
                self._accounts.values(),
                key=lambda account: (account.tenant_id, account.resource),
            )
