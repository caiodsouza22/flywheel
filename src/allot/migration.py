"""Config migration helpers between allot document versions."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Mapping

from allot.errors import ConfigError


Migration = Callable[[dict[str, Any]], dict[str, Any]]


def _ensure_dict(data: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(data, Mapping):
        raise ConfigError("migration payload must be a mapping")
    return dict(data)


def migrate_v0_to_v1(data: Mapping[str, Any]) -> dict[str, Any]:
    """Promote a legacy flat document into versioned config shape."""
    payload = _ensure_dict(data)
    if int(payload.get("version", 0)) >= 1:
        return payload
    tenants = payload.get("tenants", [])
    resources = payload.get("resources", [])
    # Legacy used "limits" instead of quotas.
    quotas = payload.get("quotas", payload.get("limits", []))
    budgets = payload.get("budgets", [])
    return {
        "version": 1,
        "tenants": list(tenants),
        "resources": list(resources),
        "quotas": list(quotas),
        "budgets": list(budgets),
    }


def migrate_normalize_softness(data: Mapping[str, Any]) -> dict[str, Any]:
    payload = deepcopy(_ensure_dict(data))
    for quota in payload.get("quotas", []):
        if isinstance(quota, dict) and "softness" not in quota:
            quota["softness"] = "hard"
    for budget in payload.get("budgets", []):
        if isinstance(budget, dict) and "softness" not in budget:
            budget["softness"] = "hard"
    payload["version"] = int(payload.get("version", 1))
    return payload


class MigrationPipeline:
    def __init__(self, migrations: list[Migration] | None = None) -> None:
        self._migrations = list(migrations or [])

    def add(self, migration: Migration) -> None:
        self._migrations.append(migration)

    def run(self, data: Mapping[str, Any]) -> dict[str, Any]:
        current = _ensure_dict(data)
        for migration in self._migrations:
            current = migration(current)
            if not isinstance(current, dict):
                raise ConfigError("migration must return a dict")
        return current


def default_pipeline() -> MigrationPipeline:
    pipeline = MigrationPipeline()
    pipeline.add(migrate_v0_to_v1)
    pipeline.add(migrate_normalize_softness)
    return pipeline


def detect_version(data: Mapping[str, Any]) -> int:
    payload = _ensure_dict(data)
    return int(payload.get("version", 0))
