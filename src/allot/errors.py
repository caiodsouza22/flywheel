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
