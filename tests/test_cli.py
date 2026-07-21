"""Tests for the allot CLI."""

from __future__ import annotations

import json
from pathlib import Path

from allot.cli import main


SAMPLE = {
    "version": 1,
    "tenants": [{"id": "acme", "weight": 1.0}],
    "resources": [{"name": "api", "capacity": 100}],
    "quotas": [{"tenant_id": "acme", "resource": "api", "limit": 50}],
    "budgets": [
        {
            "tenant_id": "acme",
            "resource": "api",
            "allowance": 20,
            "window_seconds": 3600,
        }
    ],
}


def test_show_config(tmp_path: Path, capsys) -> None:
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps(SAMPLE), encoding="utf-8")
    code = main(["show-config", str(path)])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["tenants"][0]["id"] == "acme"


def test_allocate_success_and_deny(tmp_path: Path, capsys) -> None:
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps(SAMPLE), encoding="utf-8")
    ok = main(
        [
            "allocate",
            str(path),
            "--tenant",
            "acme",
            "--resource",
            "api",
            "--amount",
            "5",
        ]
    )
    assert ok == 0
    denied = main(
        [
            "allocate",
            str(path),
            "--tenant",
            "acme",
            "--resource",
            "api",
            "--amount",
            "100",
        ]
    )
    # Fresh engine each invocation, so second call is independent; use huge amount vs budget.
    # Budget allowance is 20, so 100 should deny.
    assert denied == 2
    out = capsys.readouterr().out
    assert "granted" in out or "denied" in out
