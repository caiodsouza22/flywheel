"""Tests for extended CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

from allot.cli import main


SAMPLE = {
    "version": 1,
    "tenants": [{"id": "acme", "weight": 1.0}, {"id": "beta", "weight": 1.0}],
    "resources": [{"name": "api_calls", "capacity": 1000}],
    "quotas": [
        {"tenant_id": "acme", "resource": "api_calls", "limit": 100},
        {"tenant_id": "beta", "resource": "api_calls", "limit": 100},
    ],
    "budgets": [
        {
            "tenant_id": "acme",
            "resource": "api_calls",
            "allowance": 50,
            "window_seconds": 3600,
        },
        {
            "tenant_id": "beta",
            "resource": "api_calls",
            "allowance": 50,
            "window_seconds": 3600,
        },
    ],
}


def _write(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_simulate_command(tmp_path: Path, capsys) -> None:
    path = _write(tmp_path, SAMPLE)
    code = main(
        [
            "simulate",
            str(path),
            "--tenant",
            "acme",
            "--resource",
            "api_calls",
            "--amount",
            "10",
            "--count",
            "3",
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "simulation report" in out
    assert "granted_total" in out


def test_report_command(tmp_path: Path, capsys) -> None:
    path = _write(tmp_path, SAMPLE)
    code = main(["report", str(path), "--resource", "api_calls", "--amount", "5"])
    assert code == 0
    out = capsys.readouterr().out
    assert "system report" in out
    assert "acme" in out


def test_migrate_config_command(tmp_path: Path, capsys) -> None:
    legacy = {
        "tenants": [{"id": "acme"}],
        "resources": [{"name": "api"}],
        "limits": [{"tenant_id": "acme", "resource": "api", "limit": 9}],
    }
    path = _write(tmp_path, legacy)
    code = main(["migrate-config", str(path)])
    assert code == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["version"] == 1
    assert payload["quotas"][0]["limit"] == 9
