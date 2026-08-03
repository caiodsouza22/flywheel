"""Human-readable and structured allocation reports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from allot.models import AllocationDecision, DecisionKind
from allot.simulation import SimulationReport
from allot.store import Store
from allot.aggregator import UsageAggregator, enumerate_lifetime_keys


@dataclass(frozen=True, slots=True)
class TenantReport:
    tenant_id: str
    granted: float
    denied: int
    requested: float

    @property
    def success_rate(self) -> float:
        if self.requested <= 0:
            return 0.0
        return self.granted / self.requested


@dataclass(frozen=True, slots=True)
class SystemReport:
    tenant_reports: tuple[TenantReport, ...]
    usage_total: float
    denial_rate: float

    def to_dict(self) -> dict:
        return {
            "usage_total": self.usage_total,
            "denial_rate": self.denial_rate,
            "tenants": [
                {
                    "tenant_id": item.tenant_id,
                    "granted": item.granted,
                    "denied": item.denied,
                    "requested": item.requested,
                    "success_rate": item.success_rate,
                }
                for item in self.tenant_reports
            ],
        }


def build_tenant_reports(decisions: Iterable[AllocationDecision]) -> list[TenantReport]:
    buckets: dict[str, list[AllocationDecision]] = {}
    for decision in decisions:
        buckets.setdefault(decision.tenant_id, []).append(decision)
    reports: list[TenantReport] = []
    for tenant_id, items in sorted(buckets.items()):
        reports.append(
            TenantReport(
                tenant_id=tenant_id,
                granted=sum(item.granted for item in items),
                denied=sum(1 for item in items if item.kind is DecisionKind.DENIED),
                requested=sum(item.requested for item in items),
            )
        )
    return reports


def build_system_report(
    store: Store,
    decisions: Iterable[AllocationDecision],
) -> SystemReport:
    decision_list = list(decisions)
    tenant_reports = tuple(build_tenant_reports(decision_list))
    denied = sum(1 for item in decision_list if item.kind is DecisionKind.DENIED)
    denial_rate = (denied / len(decision_list)) if decision_list else 0.0
    usage_total = UsageAggregator(store).total(enumerate_lifetime_keys(store))
    return SystemReport(
        tenant_reports=tenant_reports,
        usage_total=usage_total,
        denial_rate=denial_rate,
    )


def render_text_report(report: SystemReport) -> str:
    lines = [
        "allot system report",
        f"usage_total={report.usage_total:.2f}",
        f"denial_rate={report.denial_rate:.2%}",
        "tenants:",
    ]
    for tenant in report.tenant_reports:
        lines.append(
            f"  - {tenant.tenant_id}: granted={tenant.granted:.2f} "
            f"requested={tenant.requested:.2f} denied={tenant.denied} "
            f"success_rate={tenant.success_rate:.2%}"
        )
    return "\n".join(lines) + "\n"


def render_simulation_report(report: SimulationReport) -> str:
    lines = [
        "allot simulation report",
        f"steps={len(report.steps)}",
        f"granted_total={report.granted_total:.2f}",
        f"denied_count={report.denied_count}",
        f"denial_rate={report.denial_rate():.2%}",
        "by_tenant:",
    ]
    for tenant_id, granted in sorted(report.by_tenant().items()):
        lines.append(f"  - {tenant_id}: granted={granted:.2f}")
    return "\n".join(lines) + "\n"
