"""Point-in-time snapshots of store configuration and usage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from allot.clock import Clock, SystemClock
from allot.config import dump_config_dict, load_config_dict
from allot.serialization import dumps, to_plain
from allot.store import InMemoryStore, Store, UsageKey


@dataclass(frozen=True, slots=True)
class StoreSnapshot:
    taken_at: datetime
    config: dict[str, Any]
    usage: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "taken_at": self.taken_at.isoformat(),
            "config": self.config,
            "usage": dict(self.usage),
        }


def capture_usage(store: Store, keys: list[UsageKey]) -> dict[str, float]:
    out: dict[str, float] = {}
    for key in keys:
        label = f"{key.tenant_id}/{key.resource}/{key.window_start_iso}"
        out[label] = store.get_usage(key)
    return out


def take_snapshot(
    store: Store,
    *,
    usage_keys: list[UsageKey] | None = None,
    clock: Clock | None = None,
) -> StoreSnapshot:
    clock = clock or SystemClock()
    keys = usage_keys or []
    return StoreSnapshot(
        taken_at=clock.now(),
        config=dump_config_dict(store),
        usage=capture_usage(store, keys),
    )


def restore_snapshot(snapshot: StoreSnapshot) -> InMemoryStore:
    store = load_config_dict(snapshot.config, store=InMemoryStore())
    for label, amount in snapshot.usage.items():
        tenant_id, resource, window = label.split("/", 2)
        if amount:
            store.add_usage(UsageKey(tenant_id, resource, window), amount)
    return store


def snapshot_dumps(snapshot: StoreSnapshot) -> str:
    return dumps(to_plain(snapshot.to_dict()), indent=2)
