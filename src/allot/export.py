"""Export allocation and usage data to tabular formats."""

from __future__ import annotations

import csv
import io
from typing import Iterable

from allot.models import AllocationDecision
from allot.store import Store, UsageKey


def decisions_to_csv(decisions: Iterable[AllocationDecision]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "kind",
            "tenant_id",
            "resource",
            "requested",
            "granted",
            "remaining_quota",
            "reason",
        ],
    )
    writer.writeheader()
    for decision in decisions:
        writer.writerow(
            {
                "kind": decision.kind.value,
                "tenant_id": decision.tenant_id,
                "resource": decision.resource,
                "requested": decision.requested,
                "granted": decision.granted,
                "remaining_quota": decision.remaining_quota,
                "reason": decision.reason or "",
            }
        )
    return buffer.getvalue()


def usage_to_csv(store: Store, keys: Iterable[UsageKey]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=["tenant_id", "resource", "window_start_iso", "consumed"],
    )
    writer.writeheader()
    for key in keys:
        writer.writerow(
            {
                "tenant_id": key.tenant_id,
                "resource": key.resource,
                "window_start_iso": key.window_start_iso,
                "consumed": store.get_usage(key),
            }
        )
    return buffer.getvalue()
