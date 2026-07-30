"""SQLite-backed store for durable allot registry and usage state."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import Iterable

from allot.errors import UnknownResource, UnknownTenant
from allot.models import Budget, Quota, Resource, Softness, Tenant
from allot.store import Store, UsageKey


_SCHEMA = """
CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    weight REAL NOT NULL,
    labels_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS resources (
    name TEXT PRIMARY KEY,
    unit TEXT NOT NULL,
    capacity REAL
);
CREATE TABLE IF NOT EXISTS quotas (
    tenant_id TEXT NOT NULL,
    resource TEXT NOT NULL,
    limit_value REAL NOT NULL,
    softness TEXT NOT NULL,
    PRIMARY KEY (tenant_id, resource)
);
CREATE TABLE IF NOT EXISTS budgets (
    tenant_id TEXT NOT NULL,
    resource TEXT NOT NULL,
    allowance REAL NOT NULL,
    window_seconds INTEGER NOT NULL,
    softness TEXT NOT NULL,
    PRIMARY KEY (tenant_id, resource)
);
CREATE TABLE IF NOT EXISTS usage (
    tenant_id TEXT NOT NULL,
    resource TEXT NOT NULL,
    window_start_iso TEXT NOT NULL,
    consumed REAL NOT NULL,
    PRIMARY KEY (tenant_id, resource, window_start_iso)
);
"""


class SqliteStore(Store):
    """Thread-safe SQLite implementation of the allot Store protocol."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self._path = str(path)
        self._lock = RLock()
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(_SCHEMA)
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def put_tenant(self, tenant: Tenant) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO tenants(id, weight, labels_json)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    weight=excluded.weight,
                    labels_json=excluded.labels_json
                """,
                (tenant.id, tenant.weight, json.dumps(dict(tenant.labels))),
            )
            self._conn.commit()

    def get_tenant(self, tenant_id: str) -> Tenant:
        with self._lock:
            row = self._conn.execute(
                "SELECT id, weight, labels_json FROM tenants WHERE id = ?",
                (tenant_id,),
            ).fetchone()
            if row is None:
                raise UnknownTenant(tenant_id)
            return Tenant(
                id=row["id"],
                weight=float(row["weight"]),
                labels=json.loads(row["labels_json"]),
            )

    def list_tenants(self) -> list[Tenant]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, weight, labels_json FROM tenants ORDER BY id"
            ).fetchall()
            return [
                Tenant(
                    id=row["id"],
                    weight=float(row["weight"]),
                    labels=json.loads(row["labels_json"]),
                )
                for row in rows
            ]

    def put_resource(self, resource: Resource) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO resources(name, unit, capacity)
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    unit=excluded.unit,
                    capacity=excluded.capacity
                """,
                (resource.name, resource.unit, resource.capacity),
            )
            self._conn.commit()

    def get_resource(self, name: str) -> Resource:
        with self._lock:
            row = self._conn.execute(
                "SELECT name, unit, capacity FROM resources WHERE name = ?",
                (name,),
            ).fetchone()
            if row is None:
                raise UnknownResource(name)
            capacity = row["capacity"]
            return Resource(
                name=row["name"],
                unit=row["unit"],
                capacity=None if capacity is None else float(capacity),
            )

    def list_resources(self) -> list[Resource]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT name, unit, capacity FROM resources ORDER BY name"
            ).fetchall()
            return [
                Resource(
                    name=row["name"],
                    unit=row["unit"],
                    capacity=None if row["capacity"] is None else float(row["capacity"]),
                )
                for row in rows
            ]

    def put_quota(self, quota: Quota) -> None:
        with self._lock:
            self.get_tenant(quota.tenant_id)
            self.get_resource(quota.resource)
            self._conn.execute(
                """
                INSERT INTO quotas(tenant_id, resource, limit_value, softness)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(tenant_id, resource) DO UPDATE SET
                    limit_value=excluded.limit_value,
                    softness=excluded.softness
                """,
                (quota.tenant_id, quota.resource, quota.limit, quota.softness.value),
            )
            self._conn.commit()

    def get_quota(self, tenant_id: str, resource: str) -> Quota | None:
        with self._lock:
            row = self._conn.execute(
                """
                SELECT tenant_id, resource, limit_value, softness
                FROM quotas WHERE tenant_id = ? AND resource = ?
                """,
                (tenant_id, resource),
            ).fetchone()
            if row is None:
                return None
            return Quota(
                tenant_id=row["tenant_id"],
                resource=row["resource"],
                limit=float(row["limit_value"]),
                softness=Softness(row["softness"]),
            )

    def put_budget(self, budget: Budget) -> None:
        with self._lock:
            self.get_tenant(budget.tenant_id)
            self.get_resource(budget.resource)
            self._conn.execute(
                """
                INSERT INTO budgets(tenant_id, resource, allowance, window_seconds, softness)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(tenant_id, resource) DO UPDATE SET
                    allowance=excluded.allowance,
                    window_seconds=excluded.window_seconds,
                    softness=excluded.softness
                """,
                (
                    budget.tenant_id,
                    budget.resource,
                    budget.allowance,
                    budget.window_seconds,
                    budget.softness.value,
                ),
            )
            self._conn.commit()

    def get_budget(self, tenant_id: str, resource: str) -> Budget | None:
        with self._lock:
            row = self._conn.execute(
                """
                SELECT tenant_id, resource, allowance, window_seconds, softness
                FROM budgets WHERE tenant_id = ? AND resource = ?
                """,
                (tenant_id, resource),
            ).fetchone()
            if row is None:
                return None
            return Budget(
                tenant_id=row["tenant_id"],
                resource=row["resource"],
                allowance=float(row["allowance"]),
                window_seconds=int(row["window_seconds"]),
                softness=Softness(row["softness"]),
            )

    def get_usage(self, key: UsageKey) -> float:
        with self._lock:
            row = self._conn.execute(
                """
                SELECT consumed FROM usage
                WHERE tenant_id = ? AND resource = ? AND window_start_iso = ?
                """,
                (key.tenant_id, key.resource, key.window_start_iso),
            ).fetchone()
            return 0.0 if row is None else float(row["consumed"])

    def add_usage(self, key: UsageKey, amount: float) -> float:
        if amount < 0:
            raise ValueError("usage amount cannot be negative")
        with self._lock:
            current = self.get_usage(key)
            total = current + amount
            self._conn.execute(
                """
                INSERT INTO usage(tenant_id, resource, window_start_iso, consumed)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(tenant_id, resource, window_start_iso) DO UPDATE SET
                    consumed=excluded.consumed
                """,
                (key.tenant_id, key.resource, key.window_start_iso, total),
            )
            self._conn.commit()
            return total

    def reset_usage(self, key: UsageKey) -> None:
        with self._lock:
            self._conn.execute(
                """
                DELETE FROM usage
                WHERE tenant_id = ? AND resource = ? AND window_start_iso = ?
                """,
                (key.tenant_id, key.resource, key.window_start_iso),
            )
            self._conn.commit()

    def seed(
        self,
        *,
        tenants: Iterable[Tenant] = (),
        resources: Iterable[Resource] = (),
        quotas: Iterable[Quota] = (),
        budgets: Iterable[Budget] = (),
    ) -> None:
        for tenant in tenants:
            self.put_tenant(tenant)
        for resource in resources:
            self.put_resource(resource)
        for quota in quotas:
            self.put_quota(quota)
        for budget in budgets:
            self.put_budget(budget)

    def list_usage_keys(self) -> list[UsageKey]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT tenant_id, resource, window_start_iso
                FROM usage
                ORDER BY tenant_id, resource, window_start_iso
                """
            ).fetchall()
            return [
                UsageKey(row["tenant_id"], row["resource"], row["window_start_iso"])
                for row in rows
            ]
