"""Priority classes that bias fair-queue ordering and weights."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from allot.models import Tenant


class Priority(IntEnum):
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass(frozen=True, slots=True)
class PrioritizedTenant:
    tenant: Tenant
    priority: Priority = Priority.NORMAL

    @property
    def effective_weight(self) -> float:
        return self.tenant.weight * float(self.priority)


def compare_priority(left: PrioritizedTenant, right: PrioritizedTenant) -> int:
    if left.priority != right.priority:
        return int(left.priority) - int(right.priority)
    if left.effective_weight != right.effective_weight:
        return 1 if left.effective_weight > right.effective_weight else -1
    return 0 if left.tenant.id == right.tenant.id else (-1 if left.tenant.id < right.tenant.id else 1)


def sort_by_priority(items: list[PrioritizedTenant]) -> list[PrioritizedTenant]:
    return sorted(
        items,
        key=lambda item: (-int(item.priority), -item.effective_weight, item.tenant.id),
    )
