"""Store and engine adapters."""

from allot.adapters.dict_store import DictStoreAdapter
from allot.adapters.file_store import FileStore
from allot.adapters.readonly import ReadOnlyStore
from allot.adapters.sqlite_store import SqliteStore

__all__ = ["DictStoreAdapter", "FileStore", "ReadOnlyStore", "SqliteStore"]
