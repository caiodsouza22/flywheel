"""Tests for lease manager and fencing tokens."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from allot import FrozenClock, LeaseConflict, LeaseManager, LeaseNotFound, StaleFencingToken


@pytest.fixture
def clock() -> FrozenClock:
    return FrozenClock(datetime(2024, 6, 1, 10, 0, tzinfo=timezone.utc))


@pytest.fixture
def leases(clock: FrozenClock) -> LeaseManager:
    return LeaseManager(clock=clock)


def test_acquire_and_check_token(leases: LeaseManager) -> None:
    lease = leases.acquire("shard-1", "worker-a", ttl_seconds=30)
    assert lease.fencing_token == 1
    assert leases.check_token(lease.id, 1).owner == "worker-a"


def test_conflict_on_active_lease(leases: LeaseManager) -> None:
    leases.acquire("shard-1", "worker-a", ttl_seconds=30)
    with pytest.raises(LeaseConflict):
        leases.acquire("shard-1", "worker-b", ttl_seconds=30)


def test_renew_bumps_fencing_token(leases: LeaseManager, clock: FrozenClock) -> None:
    lease = leases.acquire("shard-1", "worker-a", ttl_seconds=30)
    renewed = leases.renew(lease.id, ttl_seconds=30, fencing_token=1)
    assert renewed.fencing_token == 2
    with pytest.raises(StaleFencingToken):
        leases.renew(lease.id, ttl_seconds=30, fencing_token=1)


def test_expired_lease_can_be_reacquired(leases: LeaseManager, clock: FrozenClock) -> None:
    lease = leases.acquire("shard-1", "worker-a", ttl_seconds=10)
    clock.advance(11)
    with pytest.raises(LeaseNotFound):
        leases.get(lease.id)
    again = leases.acquire("shard-1", "worker-b", ttl_seconds=10)
    assert again.owner == "worker-b"
    assert again.fencing_token == 2


def test_release_requires_current_token(leases: LeaseManager) -> None:
    lease = leases.acquire("shard-1", "worker-a", ttl_seconds=30)
    with pytest.raises(StaleFencingToken):
        leases.release(lease.id, fencing_token=99)
    leases.release(lease.id, fencing_token=1)
    assert leases.get_by_key("shard-1") is None
