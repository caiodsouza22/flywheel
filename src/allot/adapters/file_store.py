"""JSON-file persistence wrapper around InMemoryStore."""

from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from typing import Any

from allot.config import dump_config_dict, load_config_dict
from allot.errors import AllotError
from allot.models import Budget, Quota, Resource, Tenant
from allot.store import InMemoryStore, Store, UsageKey


class FileStoreError(AllotError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class FileStore(Store):
    """Persists registry + usage to a single JSON document on each mutation."""

    def __init__(self, path: str | Path, *, autosave: bool = True) -> None:
        self._path = Path(path)
        self._autosave = autosave
        self._lock = RLock()
        self._inner = InMemoryStore()
        if self._path.exists():
            self.load()

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> None:
        with self._lock:
            try:
                payload = json.loads(self._path.read_text(encoding="utf-8"))
            except OSError as exc:
                raise FileStoreError(f"cannot read {self._path}") from exc
            except json.JSONDecodeError as exc:
                raise FileStoreError(f"invalid JSON in {self._path}") from exc
            self._inner = InMemoryStore()
            config = payload.get("config", payload)
            load_config_dict(config, store=self._inner)
            for label, amount in payload.get("usage", {}).items():
                tenant_id, resource, window = str(label).split("/", 2)
                if float(amount) > 0:
                    self._inner.add_usage(
                        UsageKey(tenant_id, resource, window),
                        float(amount),
                    )

    def save(self) -> None:
        with self._lock:
            usage: dict[str, float] = {}
            for tenant in self._inner.list_tenants():
                for resource in self._inner.list_resources():
                    key = UsageKey(tenant.id, resource.name, "lifetime")
                    amount = self._inner.get_usage(key)
                    if amount:
                        usage[f"{tenant.id}/{resource.name}/lifetime"] = amount
                    pool_key = UsageKey("*", resource.name, "lifetime")
                    pool_amount = self._inner.get_usage(pool_key)
                    if pool_amount:
                        usage[f"*/{resource.name}/lifetime"] = pool_amount
            payload: dict[str, Any] = {
                "config": dump_config_dict(self._inner),
                "usage": usage,
            }
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_suffix(self._path.suffix + ".tmp")
            tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
            tmp.replace(self._path)

    def _maybe_save(self) -> None:
        if self._autosave:
            self.save()

    def put_tenant(self, tenant: Tenant) -> None:
        with self._lock:
            self._inner.put_tenant(tenant)
            self._maybe_save()

    def get_tenant(self, tenant_id: str) -> Tenant:
        return self._inner.get_tenant(tenant_id)

    def list_tenants(self) -> list[Tenant]:
        return self._inner.list_tenants()

    def put_resource(self, resource: Resource) -> None:
        with self._lock:
            self._inner.put_resource(resource)
            self._maybe_save()

    def get_resource(self, name: str) -> Resource:
        return self._inner.get_resource(name)

    def list_resources(self) -> list[Resource]:
        return self._inner.list_resources()

    def put_quota(self, quota: Quota) -> None:
        with self._lock:
            self._inner.put_quota(quota)
            self._maybe_save()

    def get_quota(self, tenant_id: str, resource: str) -> Quota | None:
        return self._inner.get_quota(tenant_id, resource)

    def put_budget(self, budget: Budget) -> None:
        with self._lock:
            self._inner.put_budget(budget)
            self._maybe_save()

    def get_budget(self, tenant_id: str, resource: str) -> Budget | None:
        return self._inner.get_budget(tenant_id, resource)

    def get_usage(self, key: UsageKey) -> float:
        return self._inner.get_usage(key)

    def add_usage(self, key: UsageKey, amount: float) -> float:
        with self._lock:
            total = self._inner.add_usage(key, amount)
            self._maybe_save()
            return total

    def reset_usage(self, key: UsageKey) -> None:
        with self._lock:
            self._inner.reset_usage(key)
            self._maybe_save()
