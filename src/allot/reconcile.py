"""Reconcile store usage against an expected external ledger."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from allot.store import Store, UsageKey


@dataclass(frozen=True, slots=True)
class UsageExpectation:
    tenant_id: str
    resource: str
    window_start_iso: str
    expected: float

    def key(self) -> UsageKey:
        return UsageKey(self.tenant_id, self.resource, self.window_start_iso)


@dataclass(frozen=True, slots=True)
class UsageDrift:
    key: UsageKey
    actual: float
    expected: float

    @property
    def delta(self) -> float:
        return self.actual - self.expected


@dataclass(frozen=True, slots=True)
class ReconcileReport:
    matched: int
    drifts: tuple[UsageDrift, ...]
    missing_in_store: tuple[UsageExpectation, ...]

    @property
    def ok(self) -> bool:
        return not self.drifts and not self.missing_in_store


def reconcile_usage(
    store: Store,
    expectations: Iterable[UsageExpectation],
    *,
    tolerance: float = 0.0,
) -> ReconcileReport:
    if tolerance < 0:
        raise ValueError("tolerance cannot be negative")

    drifts: list[UsageDrift] = []
    missing: list[UsageExpectation] = []
    matched = 0

    for expectation in expectations:
        actual = store.get_usage(expectation.key())
        # get_usage returns 0 for missing keys; treat explicit expected>0 with
        # actual 0 as drift unless both are zero.
        if abs(actual - expectation.expected) <= tolerance:
            matched += 1
            continue
        if actual == 0.0 and expectation.expected != 0.0:
            missing.append(expectation)
        drifts.append(
            UsageDrift(key=expectation.key(), actual=actual, expected=expectation.expected)
        )

    return ReconcileReport(
        matched=matched,
        drifts=tuple(drifts),
        missing_in_store=tuple(missing),
    )


def apply_corrections(
    store: Store,
    drifts: Iterable[UsageDrift],
    *,
    mode: str = "set_expected",
) -> int:
    """Correct store usage for drifted keys.

    mode:
      - set_expected: reset then add expected value
      - add_delta: add (-delta) to move actual toward expected
    """
    corrected = 0
    for drift in drifts:
        if mode == "set_expected":
            store.reset_usage(drift.key)
            if drift.expected:
                store.add_usage(drift.key, drift.expected)
            corrected += 1
        elif mode == "add_delta":
            delta = drift.expected - drift.actual
            if delta > 0:
                store.add_usage(drift.key, delta)
            elif delta < 0:
                # Store API only supports add/reset; emulate reduction via reset+set.
                store.reset_usage(drift.key)
                if drift.expected:
                    store.add_usage(drift.key, drift.expected)
            corrected += 1
        else:
            raise ValueError(f"unknown correction mode: {mode}")
    return corrected


def expectations_from_mapping(
    mapping: Mapping[tuple[str, str, str], float],
) -> list[UsageExpectation]:
    return [
        UsageExpectation(
            tenant_id=tenant_id,
            resource=resource,
            window_start_iso=window,
            expected=value,
        )
        for (tenant_id, resource, window), value in mapping.items()
    ]
