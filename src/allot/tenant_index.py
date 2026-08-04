"""Secondary indexes for looking up tenants by label and tier."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock

from allot.errors import UnknownTenant
from allot.models import Tenant
from allot.store import Store


@dataclass
class TenantIndex:
    """In-memory inverted index over tenant labels."""

    _by_id: dict[str, Tenant] = field(default_factory=dict)
    _by_label: dict[tuple[str, str], set[str]] = field(default_factory=dict)
    _lock: RLock = field(default_factory=RLock)

    def rebuild(self, store: Store) -> None:
        with self._lock:
            self._by_id.clear()
            self._by_label.clear()
            for tenant in store.list_tenants():
                self._index_locked(tenant)

    def upsert(self, tenant: Tenant) -> None:
        with self._lock:
            old = self._by_id.get(tenant.id)
            if old is not None:
                self._unindex_locked(old)
            self._index_locked(tenant)

    def remove(self, tenant_id: str) -> None:
        with self._lock:
            tenant = self._by_id.get(tenant_id)
            if tenant is None:
                raise UnknownTenant(tenant_id)
            self._unindex_locked(tenant)

    def get(self, tenant_id: str) -> Tenant:
        with self._lock:
            try:
                return self._by_id[tenant_id]
            except KeyError as exc:
                raise UnknownTenant(tenant_id) from exc

    def find_by_label(self, key: str, value: str) -> list[Tenant]:
        with self._lock:
            ids = self._by_label.get((key, value), set())
            return sorted((self._by_id[item] for item in ids), key=lambda tenant: tenant.id)

    def find_by_tier(self, tier: str) -> list[Tenant]:
        return self.find_by_label("tier", tier)

    def label_keys(self) -> list[str]:
        with self._lock:
            return sorted({key for key, _value in self._by_label})

    def counts_by_label(self, key: str) -> dict[str, int]:
        with self._lock:
            counts: dict[str, int] = {}
            for (label_key, label_value), ids in self._by_label.items():
                if label_key != key:
                    continue
                counts[label_value] = len(ids)
            return dict(sorted(counts.items()))

    def _index_locked(self, tenant: Tenant) -> None:
        self._by_id[tenant.id] = tenant
        for key, value in tenant.labels.items():
            self._by_label.setdefault((key, value), set()).add(tenant.id)

    def _unindex_locked(self, tenant: Tenant) -> None:
        self._by_id.pop(tenant.id, None)
        for key, value in tenant.labels.items():
            bucket = self._by_label.get((key, value))
            if not bucket:
                continue
            bucket.discard(tenant.id)
            if not bucket:
                del self._by_label[(key, value)]
