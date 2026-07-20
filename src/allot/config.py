"""Load allot configuration documents into an in-memory store."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from allot.errors import ConfigError
from allot.serialization import (
    budget_from_dict,
    quota_from_dict,
    resource_from_dict,
    tenant_from_dict,
)
from allot.store import InMemoryStore, Store


@dataclass(frozen=True, slots=True)
class AllotConfig:
    """Validated configuration snapshot."""

    version: int
    tenants: tuple[Any, ...]
    resources: tuple[Any, ...]
    quotas: tuple[Any, ...]
    budgets: tuple[Any, ...]


def parse_config(data: Mapping[str, Any]) -> AllotConfig:
    if not isinstance(data, Mapping):
        raise ConfigError("config root must be a mapping")
    version = int(data.get("version", 1))
    if version != 1:
        raise ConfigError(f"unsupported config version: {version}")

    try:
        tenants = tuple(tenant_from_dict(item) for item in data.get("tenants", []))
        resources = tuple(resource_from_dict(item) for item in data.get("resources", []))
        quotas = tuple(quota_from_dict(item) for item in data.get("quotas", []))
        budgets = tuple(budget_from_dict(item) for item in data.get("budgets", []))
    except (KeyError, TypeError, ValueError) as exc:
        raise ConfigError(f"invalid config payload: {exc}") from exc

    return AllotConfig(
        version=version,
        tenants=tenants,
        resources=resources,
        quotas=quotas,
        budgets=budgets,
    )


def load_config_dict(data: Mapping[str, Any], *, store: Store | None = None) -> Store:
    config = parse_config(data)
    target: Store = store or InMemoryStore()
    if isinstance(target, InMemoryStore):
        target.seed(
            tenants=config.tenants,
            resources=config.resources,
            quotas=config.quotas,
            budgets=config.budgets,
        )
        return target

    for tenant in config.tenants:
        target.put_tenant(tenant)
    for resource in config.resources:
        target.put_resource(resource)
    for quota in config.quotas:
        target.put_quota(quota)
    for budget in config.budgets:
        target.put_budget(budget)
    return target


def load_config_file(path: str | Path, *, store: Store | None = None) -> Store:
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read config file: {file_path}") from exc
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"config file is not valid JSON: {file_path}") from exc
    if not isinstance(payload, Mapping):
        raise ConfigError("config JSON root must be an object")
    return load_config_dict(payload, store=store)


def dump_config_dict(store: Store) -> dict[str, Any]:
    from allot.serialization import (
        budget_to_dict,
        quota_to_dict,
        resource_to_dict,
        tenant_to_dict,
    )

    tenants = [tenant_to_dict(tenant) for tenant in store.list_tenants()]
    resources = [resource_to_dict(resource) for resource in store.list_resources()]
    quotas = []
    budgets = []
    for tenant in store.list_tenants():
        for resource in store.list_resources():
            quota = store.get_quota(tenant.id, resource.name)
            if quota is not None:
                quotas.append(quota_to_dict(quota))
            budget = store.get_budget(tenant.id, resource.name)
            if budget is not None:
                budgets.append(budget_to_dict(budget))
    return {
        "version": 1,
        "tenants": tenants,
        "resources": resources,
        "quotas": quotas,
        "budgets": budgets,
    }
