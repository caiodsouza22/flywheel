"""Health checks for allot runtime components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from allot.store import Store


@dataclass(frozen=True, slots=True)
class HealthCheck:
    name: str
    ok: bool
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class HealthReport:
    checks: tuple[HealthCheck, ...]

    @property
    def healthy(self) -> bool:
        return all(check.ok for check in self.checks)


def check_store(store: Store) -> HealthCheck:
    try:
        tenants = store.list_tenants()
        resources = store.list_resources()
    except Exception as exc:  # pragma: no cover - defensive
        return HealthCheck(name="store", ok=False, detail=str(exc))
    return HealthCheck(
        name="store",
        ok=True,
        detail=f"tenants={len(tenants)} resources={len(resources)}",
    )


def run_health(
    store: Store,
    extra: list[Callable[[], HealthCheck]] | None = None,
) -> HealthReport:
    checks = [check_store(store)]
    for factory in extra or []:
        checks.append(factory())
    return HealthReport(checks=tuple(checks))
