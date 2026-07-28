"""Tests for policy registry."""

from __future__ import annotations

import pytest

from allot.policy_registry import PolicyRegistry, UnknownPolicy
from allot.policies import StrictPolicy


def test_default_policies_and_custom() -> None:
    registry = PolicyRegistry()
    assert "strict" in registry.names()
    assert isinstance(registry.get("strict"), StrictPolicy)
    registry.register("custom", StrictPolicy())
    assert registry.get("custom") is not None
    with pytest.raises(UnknownPolicy):
        registry.get("missing")
