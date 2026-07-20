"""Soft reservation holds that can later be committed or released."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from threading import RLock

from allot.clock import Clock, SystemClock
from allot.errors import ReservationExpired, ReservationNotFound
from allot.models import AllocationDecision, AllocationRequest, DecisionKind
from allot.store import Store, UsageKey


class ReservationState(str, Enum):
    HELD = "held"
    COMMITTED = "committed"
    RELEASED = "released"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class Reservation:
    id: str
    tenant_id: str
    resource: str
    amount: float
    state: ReservationState
    expires_at: datetime
    created_at: datetime
    fencing_note: str | None = None

    def is_terminal(self) -> bool:
        return self.state in {
            ReservationState.COMMITTED,
            ReservationState.RELEASED,
            ReservationState.EXPIRED,
        }


class ReservationBook:
    """Holds capacity temporarily without permanently consuming lifetime quota.

    Held amount is tracked under a dedicated usage namespace so the allocation
    engine's lifetime counters remain untouched until commit.
    """

    HOLD_PREFIX = "hold:"

    def __init__(self, store: Store, *, clock: Clock | None = None) -> None:
        self._store = store
        self._clock = clock or SystemClock()
        self._reservations: dict[str, Reservation] = {}
        self._lock = RLock()

    def hold(
        self,
        tenant_id: str,
        resource: str,
        amount: float,
        *,
        ttl_seconds: float,
        reservation_id: str | None = None,
    ) -> Reservation:
        if amount <= 0:
            raise ValueError("amount must be positive")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")

        # Ensure tenant/resource exist.
        self._store.get_tenant(tenant_id)
        self._store.get_resource(resource)

        now = self._clock.now()
        with self._lock:
            self._expire_locked(now)
            reservation = Reservation(
                id=reservation_id or str(uuid.uuid4()),
                tenant_id=tenant_id,
                resource=resource,
                amount=amount,
                state=ReservationState.HELD,
                expires_at=now + timedelta(seconds=ttl_seconds),
                created_at=now,
            )
            key = self._hold_key(reservation)
            self._store.add_usage(key, amount)
            self._reservations[reservation.id] = reservation
            return reservation

    def commit(self, reservation_id: str) -> AllocationDecision:
        now = self._clock.now()
        with self._lock:
            reservation = self._require_held_locked(reservation_id, now)
            hold_key = self._hold_key(reservation)
            held = self._store.get_usage(hold_key)
            if held < reservation.amount:
                # Defensive: usage missing somehow.
                raise ReservationExpired(reservation_id)
            # Move hold into lifetime usage.
            self._store.add_usage(
                UsageKey(reservation.tenant_id, reservation.resource, "lifetime"),
                reservation.amount,
            )
            # Clear hold by resetting (then leave at zero).
            self._store.reset_usage(hold_key)
            committed = Reservation(
                id=reservation.id,
                tenant_id=reservation.tenant_id,
                resource=reservation.resource,
                amount=reservation.amount,
                state=ReservationState.COMMITTED,
                expires_at=reservation.expires_at,
                created_at=reservation.created_at,
            )
            self._reservations[reservation.id] = committed
            return AllocationDecision(
                kind=DecisionKind.GRANTED,
                tenant_id=reservation.tenant_id,
                resource=reservation.resource,
                requested=reservation.amount,
                granted=reservation.amount,
                reason="reservation_committed",
            )

    def release(self, reservation_id: str) -> Reservation:
        now = self._clock.now()
        with self._lock:
            reservation = self._require_held_locked(reservation_id, now)
            self._store.reset_usage(self._hold_key(reservation))
            released = Reservation(
                id=reservation.id,
                tenant_id=reservation.tenant_id,
                resource=reservation.resource,
                amount=reservation.amount,
                state=ReservationState.RELEASED,
                expires_at=reservation.expires_at,
                created_at=reservation.created_at,
            )
            self._reservations[reservation.id] = released
            return released

    def get(self, reservation_id: str) -> Reservation:
        now = self._clock.now()
        with self._lock:
            self._expire_locked(now)
            reservation = self._reservations.get(reservation_id)
            if reservation is None:
                raise ReservationNotFound(reservation_id)
            return reservation

    def held_amount(self, tenant_id: str, resource: str) -> float:
        now = self._clock.now()
        with self._lock:
            self._expire_locked(now)
            total = 0.0
            for reservation in self._reservations.values():
                if (
                    reservation.state is ReservationState.HELD
                    and reservation.tenant_id == tenant_id
                    and reservation.resource == resource
                ):
                    total += reservation.amount
            return total

    def active(self) -> list[Reservation]:
        now = self._clock.now()
        with self._lock:
            self._expire_locked(now)
            return [
                r
                for r in sorted(self._reservations.values(), key=lambda item: item.id)
                if r.state is ReservationState.HELD
            ]

    def as_request(self, reservation_id: str) -> AllocationRequest:
        reservation = self.get(reservation_id)
        return AllocationRequest(
            tenant_id=reservation.tenant_id,
            resource=reservation.resource,
            amount=reservation.amount,
        )

    def _hold_key(self, reservation: Reservation) -> UsageKey:
        return UsageKey(
            reservation.tenant_id,
            reservation.resource,
            f"{self.HOLD_PREFIX}{reservation.id}",
        )

    def _require_held_locked(self, reservation_id: str, now: datetime) -> Reservation:
        self._expire_locked(now)
        reservation = self._reservations.get(reservation_id)
        if reservation is None:
            raise ReservationNotFound(reservation_id)
        if reservation.state is ReservationState.EXPIRED:
            raise ReservationExpired(reservation_id)
        if reservation.state is not ReservationState.HELD:
            raise ReservationExpired(reservation_id)
        if now >= reservation.expires_at:
            self._expire_one_locked(reservation)
            raise ReservationExpired(reservation_id)
        return reservation

    def _expire_locked(self, now: datetime) -> None:
        for reservation in list(self._reservations.values()):
            if reservation.state is ReservationState.HELD and now >= reservation.expires_at:
                self._expire_one_locked(reservation)

    def _expire_one_locked(self, reservation: Reservation) -> None:
        self._store.reset_usage(self._hold_key(reservation))
        self._reservations[reservation.id] = Reservation(
            id=reservation.id,
            tenant_id=reservation.tenant_id,
            resource=reservation.resource,
            amount=reservation.amount,
            state=ReservationState.EXPIRED,
            expires_at=reservation.expires_at,
            created_at=reservation.created_at,
        )
