"""Aggregate usage across tenants, resources, and windows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from allot.store import Store, UsageKey


@dataclass(frozen=True, slots=True)
class UsageSlice:
    tenant_id: str
    resource: str
    window_start_iso: str
    consumed: float


@dataclass(frozen=True, slots=True)
class AggregateRow:
    group_key: str
    consumed: float
    samples: int


@dataclass
class UsageAggregator:
    store: Store

    def collect(self, keys: Iterable[UsageKey]) -> list[UsageSlice]:
        slices: list[UsageSlice] = []
        for key in keys:
            slices.append(
                UsageSlice(
                    tenant_id=key.tenant_id,
                    resource=key.resource,
                    window_start_iso=key.window_start_iso,
                    consumed=self.store.get_usage(key),
                )
            )
        return slices

    def by_tenant(self, keys: Iterable[UsageKey]) -> list[AggregateRow]:
        return self._group(keys, lambda item: item.tenant_id)

    def by_resource(self, keys: Iterable[UsageKey]) -> list[AggregateRow]:
        return self._group(keys, lambda item: item.resource)

    def by_tenant_resource(self, keys: Iterable[UsageKey]) -> list[AggregateRow]:
        return self._group(keys, lambda item: f"{item.tenant_id}/{item.resource}")

    def top_n(
        self,
        keys: Iterable[UsageKey],
        *,
        n: int,
        group: str = "tenant",
    ) -> list[AggregateRow]:
        if n < 1:
            raise ValueError("n must be >= 1")
        if group == "tenant":
            rows = self.by_tenant(keys)
        elif group == "resource":
            rows = self.by_resource(keys)
        elif group == "tenant_resource":
            rows = self.by_tenant_resource(keys)
        else:
            raise ValueError(f"unknown group: {group}")
        return sorted(rows, key=lambda row: (-row.consumed, row.group_key))[:n]

    def total(self, keys: Iterable[UsageKey]) -> float:
        return sum(item.consumed for item in self.collect(keys))

    def _group(
        self,
        keys: Iterable[UsageKey],
        key_fn: Callable[[UsageSlice], str],
    ) -> list[AggregateRow]:
        buckets: dict[str, list[float]] = {}
        for item in self.collect(keys):
            group_key = key_fn(item)
            buckets.setdefault(group_key, []).append(item.consumed)
        rows = [
            AggregateRow(
                group_key=group_key,
                consumed=sum(values),
                samples=len(values),
            )
            for group_key, values in buckets.items()
        ]
        return sorted(rows, key=lambda row: row.group_key)


def enumerate_lifetime_keys(store: Store) -> list[UsageKey]:
    keys: list[UsageKey] = []
    for tenant in store.list_tenants():
        for resource in store.list_resources():
            keys.append(UsageKey(tenant.id, resource.name, "lifetime"))
    for resource in store.list_resources():
        keys.append(UsageKey("*", resource.name, "lifetime"))
    return keys
