"""Tests for extra policies."""

from __future__ import annotations

from allot import Softness, StrictPolicy, Tenant
from allot.policies import PolicyContext
from allot.policies_extra import (
    AllOrNothingPolicy,
    CapPolicy,
    PreferTenantPolicy,
    ReserveHeadroomPolicy,
)


def _ctx(
    *,
    tenant: str = "acme",
    requested: float = 10,
    pool: float | None = 10,
) -> PolicyContext:
    return PolicyContext(
        tenant=Tenant(id=tenant, weight=1),
        requested=requested,
        remaining_quota=None,
        remaining_budget=None,
        remaining_pool=pool,
        softness=Softness.HARD,
    )


def test_reserve_headroom_blocks_full_drain() -> None:
    policy = ReserveHeadroomPolicy(headroom_ratio=0.2)
    result = policy.decide(_ctx(requested=10, pool=10))
    assert result.granted == 0


def test_prefer_and_cap_and_all_or_nothing() -> None:
    prefer = PreferTenantPolicy(preferred_tenant_id="acme", inner=StrictPolicy())
    assert prefer.decide(_ctx(tenant="acme", requested=4, pool=4)).granted == 4
    other = prefer.decide(_ctx(tenant="beta", requested=4, pool=4))
    assert other.granted == 0
    capped = CapPolicy(max_grant=3, inner=StrictPolicy())
    result = capped.decide(_ctx(requested=10, pool=10))
    assert result.granted == 3
    assert result.reason == "capped"
    aon = AllOrNothingPolicy(inner=StrictPolicy())
    # Strict already all-or-nothing on pool; keep smoke assertion.
    assert aon.decide(_ctx(requested=2, pool=2)).granted == 2
