"""Exclusive leases with monotonically increasing fencing tokens."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import RLock

from allot.clock import Clock, SystemClock
from allot.errors import LeaseConflict, LeaseExpired, LeaseNotFound, StaleFencingToken


@dataclass(frozen=True, slots=True)
class Lease:
    """A time-bounded exclusive hold on a named resource key."""

    id: str
    resource_key: str
    owner: str
    fencing_token: int
    expires_at: datetime
    created_at: datetime

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at

    def remaining_seconds(self, now: datetime) -> float:
        return max(0.0, (self.expires_at - now).total_seconds())


class LeaseManager:
    """Issues and renews leases; fencing tokens increase on each acquire/renew."""

    def __init__(self, *, clock: Clock | None = None) -> None:
        self._clock = clock or SystemClock()
        self._leases: dict[str, Lease] = {}
        self._by_key: dict[str, str] = {}
        self._tokens: dict[str, int] = {}
        self._lock = RLock()

    def acquire(
        self,
        resource_key: str,
        owner: str,
        *,
        ttl_seconds: float,
        lease_id: str | None = None,
    ) -> Lease:
        if not resource_key:
            raise ValueError("resource_key must be non-empty")
        if not owner:
            raise ValueError("owner must be non-empty")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")

        now = self._clock.now()
        with self._lock:
            self._purge_expired_locked(now)
            existing_id = self._by_key.get(resource_key)
            if existing_id is not None:
                existing = self._leases[existing_id]
                if not existing.is_expired(now):
                    raise LeaseConflict(
                        resource_key,
                        existing.owner,
                        existing.id,
                    )

            token = self._tokens.get(resource_key, 0) + 1
            self._tokens[resource_key] = token
            lease = Lease(
                id=lease_id or str(uuid.uuid4()),
                resource_key=resource_key,
                owner=owner,
                fencing_token=token,
                expires_at=now + timedelta(seconds=ttl_seconds),
                created_at=now,
            )
            self._leases[lease.id] = lease
            self._by_key[resource_key] = lease.id
            return lease

    def renew(self, lease_id: str, *, ttl_seconds: float, fencing_token: int) -> Lease:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        now = self._clock.now()
        with self._lock:
            lease = self._require_lease_locked(lease_id, now)
            if fencing_token != lease.fencing_token:
                raise StaleFencingToken(lease_id, fencing_token, lease.fencing_token)
            token = lease.fencing_token + 1
            self._tokens[lease.resource_key] = token
            renewed = Lease(
                id=lease.id,
                resource_key=lease.resource_key,
                owner=lease.owner,
                fencing_token=token,
                expires_at=now + timedelta(seconds=ttl_seconds),
                created_at=lease.created_at,
            )
            self._leases[lease.id] = renewed
            return renewed

    def release(self, lease_id: str, *, fencing_token: int) -> None:
        now = self._clock.now()
        with self._lock:
            lease = self._require_lease_locked(lease_id, now)
            if fencing_token != lease.fencing_token:
                raise StaleFencingToken(lease_id, fencing_token, lease.fencing_token)
            self._leases.pop(lease_id, None)
            if self._by_key.get(lease.resource_key) == lease_id:
                self._by_key.pop(lease.resource_key, None)

    def get(self, lease_id: str) -> Lease:
        now = self._clock.now()
        with self._lock:
            return self._require_lease_locked(lease_id, now)

    def get_by_key(self, resource_key: str) -> Lease | None:
        now = self._clock.now()
        with self._lock:
            self._purge_expired_locked(now)
            lease_id = self._by_key.get(resource_key)
            if lease_id is None:
                return None
            return self._leases.get(lease_id)

    def check_token(self, lease_id: str, fencing_token: int) -> Lease:
        """Validate a fencing token against the live lease."""
        now = self._clock.now()
        with self._lock:
            lease = self._require_lease_locked(lease_id, now)
            if fencing_token < lease.fencing_token:
                raise StaleFencingToken(lease_id, fencing_token, lease.fencing_token)
            if fencing_token > lease.fencing_token:
                raise StaleFencingToken(lease_id, fencing_token, lease.fencing_token)
            return lease

    def active_leases(self) -> list[Lease]:
        now = self._clock.now()
        with self._lock:
            self._purge_expired_locked(now)
            return sorted(self._leases.values(), key=lambda lease: lease.resource_key)

    def _require_lease_locked(self, lease_id: str, now: datetime) -> Lease:
        self._purge_expired_locked(now)
        lease = self._leases.get(lease_id)
        if lease is None:
            # Distinguish expired-and-purged from never-existed when possible.
            raise LeaseNotFound(lease_id)
        if lease.is_expired(now):
            self._purge_one_locked(lease)
            raise LeaseExpired(lease_id)
        return lease

    def _purge_expired_locked(self, now: datetime) -> None:
        expired = [lease for lease in self._leases.values() if lease.is_expired(now)]
        for lease in expired:
            self._purge_one_locked(lease)

    def _purge_one_locked(self, lease: Lease) -> None:
        self._leases.pop(lease.id, None)
        if self._by_key.get(lease.resource_key) == lease.id:
            self._by_key.pop(lease.resource_key, None)

