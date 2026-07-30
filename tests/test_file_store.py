"""Tests for FileStore persistence."""

from __future__ import annotations

from allot import Resource, Tenant
from allot.adapters.file_store import FileStore
from allot.store import UsageKey


def test_file_store_autosave_and_reload(tmp_path) -> None:
    path = tmp_path / "state.json"
    store = FileStore(path)
    store.put_tenant(Tenant(id="acme"))
    store.put_resource(Resource(name="api", capacity=9))
    store.add_usage(UsageKey("acme", "api", "lifetime"), 4)
    assert path.exists()

    reloaded = FileStore(path)
    assert reloaded.get_tenant("acme").id == "acme"
    assert reloaded.get_usage(UsageKey("acme", "api", "lifetime")) == 4
