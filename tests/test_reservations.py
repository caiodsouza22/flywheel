"""Tests for reservation holds."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from allot import (
    DecisionKind,
    FrozenClock,
    InMemoryStore,
    ReservationBook,
    ReservationExpired,
    ReservationState,
    Resource,
    Tenant,
)
from allot.store import UsageKey


@pytest.fixture
def clock() -> FrozenClock:
    return FrozenClock(datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc))


@pytest.fixture
def book(clock: FrozenClock) -> ReservationBook:
    store = InMemoryStore()
    store.seed(
        tenants=[Tenant(id="acme")],
        resources=[Resource(name="api_calls", capacity=100)],
    )
    return ReservationBook(store, clock=clock)


def test_hold_commit_moves_to_lifetime(book: ReservationBook, clock: FrozenClock) -> None:
    reservation = book.hold("acme", "api_calls", 7, ttl_seconds=60)
    assert reservation.state is ReservationState.HELD
    assert book.held_amount("acme", "api_calls") == 7
    decision = book.commit(reservation.id)
    assert decision.kind is DecisionKind.GRANTED
    assert book.get(reservation.id).state is ReservationState.COMMITTED
    lifetime = book._store.get_usage(UsageKey("acme", "api_calls", "lifetime"))
    assert lifetime == 7


def test_release_clears_hold(book: ReservationBook) -> None:
    reservation = book.hold("acme", "api_calls", 5, ttl_seconds=60)
    released = book.release(reservation.id)
    assert released.state is ReservationState.RELEASED
    assert book.held_amount("acme", "api_calls") == 0


def test_expired_hold_cannot_commit(book: ReservationBook, clock: FrozenClock) -> None:
    reservation = book.hold("acme", "api_calls", 5, ttl_seconds=10)
    clock.advance(11)
    with pytest.raises(ReservationExpired):
        book.commit(reservation.id)
    assert book.get(reservation.id).state is ReservationState.EXPIRED
