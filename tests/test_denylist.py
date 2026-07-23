"""Tests for access lists."""

from __future__ import annotations

import pytest

from allot import AllocationRequest
from allot.denylist import AccessLists, DeniedByList


def test_denylist_and_allowlist() -> None:
    access = AccessLists()
    access.deny_tenant("bad")
    with pytest.raises(DeniedByList):
        access.check(AllocationRequest(tenant_id="bad", resource="api", amount=1))
    access.allow_tenant("acme")
    with pytest.raises(DeniedByList):
        access.check(AllocationRequest(tenant_id="other", resource="api", amount=1))
    access.check(AllocationRequest(tenant_id="acme", resource="api", amount=1))
