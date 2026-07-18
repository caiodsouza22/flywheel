"""Domain errors raised by allot."""

from __future__ import annotations


class AllotError(Exception):
    """Base error for the allot library."""


class UnknownTenant(AllotError):
    """Raised when a tenant id is not registered."""

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        super().__init__(f"unknown tenant: {tenant_id}")


class UnknownResource(AllotError):
    """Raised when a resource name is not registered."""

    def __init__(self, resource: str) -> None:
        self.resource = resource
        super().__init__(f"unknown resource: {resource}")


class QuotaExceeded(AllotError):
    """Raised when a hard quota would be breached."""

    def __init__(self, tenant_id: str, resource: str, requested: float, remaining: float) -> None:
        self.tenant_id = tenant_id
        self.resource = resource
        self.requested = requested
        self.remaining = remaining
        super().__init__(
            f"quota exceeded for tenant={tenant_id} resource={resource}: "
            f"requested={requested} remaining={remaining}"
        )


class InsufficientCapacity(AllotError):
    """Raised when global or pool capacity cannot satisfy the request."""

    def __init__(self, resource: str, requested: float, available: float) -> None:
        self.resource = resource
        self.requested = requested
        self.available = available
        super().__init__(
            f"insufficient capacity for resource={resource}: "
            f"requested={requested} available={available}"
        )


class InvalidWindow(AllotError):
    """Raised when a time window configuration is invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class LeaseError(AllotError):
    """Base error for lease operations."""


class LeaseNotFound(LeaseError):
    """Raised when a lease id is unknown."""

    def __init__(self, lease_id: str) -> None:
        self.lease_id = lease_id
        super().__init__(f"lease not found: {lease_id}")


class LeaseExpired(LeaseError):
    """Raised when an operation targets an expired lease."""

    def __init__(self, lease_id: str) -> None:
        self.lease_id = lease_id
        super().__init__(f"lease expired: {lease_id}")


class StaleFencingToken(LeaseError):
    """Raised when a fencing token is older than the current lease token."""

    def __init__(self, lease_id: str, provided: int, current: int) -> None:
        self.lease_id = lease_id
        self.provided = provided
        self.current = current
        super().__init__(
            f"stale fencing token for lease={lease_id}: provided={provided} current={current}"
        )


class LeaseConflict(LeaseError):
    """Raised when a resource key is already leased by another owner."""

    def __init__(self, resource_key: str, owner: str, lease_id: str) -> None:
        self.resource_key = resource_key
        self.owner = owner
        self.lease_id = lease_id
        super().__init__(
            f"resource_key={resource_key} already leased by owner={owner} lease_id={lease_id}"
        )


class ReservationError(AllotError):
    """Base error for reservation holds."""


class ReservationNotFound(ReservationError):
    """Raised when a reservation id is unknown."""

    def __init__(self, reservation_id: str) -> None:
        self.reservation_id = reservation_id
        super().__init__(f"reservation not found: {reservation_id}")


class ReservationExpired(ReservationError):
    """Raised when a reservation can no longer be committed."""

    def __init__(self, reservation_id: str) -> None:
        self.reservation_id = reservation_id
        super().__init__(f"reservation expired: {reservation_id}")


class ConfigError(AllotError):
    """Raised when configuration cannot be loaded or validated."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class InsufficientSlidingBudget(AllotError):
    """Raised when a sliding-window budget cannot cover a spend."""

    def __init__(
        self,
        tenant_id: str,
        resource: str,
        requested: float,
        remaining: float,
    ) -> None:
        self.tenant_id = tenant_id
        self.resource = resource
        self.requested = requested
        self.remaining = remaining
        super().__init__(
            f"sliding budget exceeded for tenant={tenant_id} resource={resource}: "
            f"requested={requested} remaining={remaining}"
        )
