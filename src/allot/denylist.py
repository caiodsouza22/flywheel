"""Denylist / allowlist controls for tenants and resources."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock

from allot.errors import AllotError
from allot.models import AllocationRequest


class DeniedByList(AllotError):
    def __init__(self, subject: str, reason: str) -> None:
        self.subject = subject
        self.reason = reason
        super().__init__(f"denied {subject}: {reason}")


@dataclass
class AccessLists:
    """Optional deny/allow sets. If an allowlist is non-empty, it is enforced."""

    denied_tenants: set[str] = field(default_factory=set)
    allowed_tenants: set[str] = field(default_factory=set)
    denied_resources: set[str] = field(default_factory=set)
    allowed_resources: set[str] = field(default_factory=set)
    _lock: RLock = field(default_factory=RLock)

    def deny_tenant(self, tenant_id: str) -> None:
        with self._lock:
            self.denied_tenants.add(tenant_id)

    def allow_tenant(self, tenant_id: str) -> None:
        with self._lock:
            self.allowed_tenants.add(tenant_id)

    def deny_resource(self, resource: str) -> None:
        with self._lock:
            self.denied_resources.add(resource)

    def allow_resource(self, resource: str) -> None:
        with self._lock:
            self.allowed_resources.add(resource)

    def check(self, request: AllocationRequest) -> None:
        with self._lock:
            if request.tenant_id in self.denied_tenants:
                raise DeniedByList(request.tenant_id, "tenant denylisted")
            if self.allowed_tenants and request.tenant_id not in self.allowed_tenants:
                raise DeniedByList(request.tenant_id, "tenant not allowlisted")
            if request.resource in self.denied_resources:
                raise DeniedByList(request.resource, "resource denylisted")
            if self.allowed_resources and request.resource not in self.allowed_resources:
                raise DeniedByList(request.resource, "resource not allowlisted")
