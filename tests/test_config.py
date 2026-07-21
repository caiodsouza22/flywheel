"""Tests for config loading and dumping."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from allot import ConfigError, load_config_dict, load_config_file, parse_config
from allot.config import dump_config_dict


SAMPLE = {
    "version": 1,
    "tenants": [{"id": "acme", "weight": 1.5}],
    "resources": [{"name": "api", "capacity": 100}],
    "quotas": [{"tenant_id": "acme", "resource": "api", "limit": 20}],
    "budgets": [
        {
            "tenant_id": "acme",
            "resource": "api",
            "allowance": 10,
            "window_seconds": 60,
        }
    ],
}


def test_parse_and_load_dict() -> None:
    config = parse_config(SAMPLE)
    assert config.version == 1
    assert len(config.tenants) == 1
    store = load_config_dict(SAMPLE)
    assert store.get_tenant("acme").weight == 1.5
    assert store.get_quota("acme", "api") is not None


def test_load_config_file_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "allot.json"
    path.write_text(json.dumps(SAMPLE), encoding="utf-8")
    store = load_config_file(path)
    dumped = dump_config_dict(store)
    assert dumped["tenants"][0]["id"] == "acme"
    assert dumped["budgets"][0]["allowance"] == 10


def test_unsupported_version() -> None:
    with pytest.raises(ConfigError, match="unsupported"):
        parse_config({"version": 99, "tenants": []})


def test_invalid_json_file(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{nope", encoding="utf-8")
    with pytest.raises(ConfigError, match="not valid JSON"):
        load_config_file(path)
