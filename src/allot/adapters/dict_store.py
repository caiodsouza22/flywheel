"""Adapter that builds an InMemoryStore from plain nested dictionaries."""

from __future__ import annotations

from typing import Any, Mapping

from allot.config import load_config_dict
from allot.store import InMemoryStore


class DictStoreAdapter:
    """Convenience builder around ``load_config_dict``."""

    @staticmethod
    def from_mapping(data: Mapping[str, Any]) -> InMemoryStore:
        return load_config_dict(data, store=InMemoryStore())  # type: ignore[return-value]
