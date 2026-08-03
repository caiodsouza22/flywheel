"""Tests for config migrations."""

from __future__ import annotations

from allot.migration import default_pipeline, detect_version, migrate_v0_to_v1


def test_migrate_legacy_limits_to_quotas() -> None:
    legacy = {
        "tenants": [{"id": "acme"}],
        "resources": [{"name": "api"}],
        "limits": [{"tenant_id": "acme", "resource": "api", "limit": 5}],
    }
    assert detect_version(legacy) == 0
    migrated = default_pipeline().run(legacy)
    assert migrated["version"] == 1
    assert migrated["quotas"][0]["softness"] == "hard"
    assert migrate_v0_to_v1(migrated)["version"] == 1
