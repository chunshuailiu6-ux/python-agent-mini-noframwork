"""短期记忆：基于内存的存储，会话级别，带 TTL 过期。"""

from __future__ import annotations

from typing import Any, Optional

from .base import BaseMemory, MemoryItem


class ShortTermMemory(BaseMemory):
    """短期记忆，使用 Python 字典存储。

    特点：
    - 进程退出即丢失。
    - 支持 TTL 过期，读写时自动清理。
    - 适合存储会话级别的临时数据。
    """

    def __init__(self) -> None:
        self._store: dict[str, MemoryItem] = {}

    def add(self, key: str, value: Any, metadata: Optional[dict] = None, ttl: Optional[int] = None) -> None:
        self._store[key] = MemoryItem(key=key, value=value, metadata=metadata or {}, ttl=ttl)

    def get(self, key: str) -> Optional[Any]:
        item = self.get_item(key)
        return item.value if item else None

    def get_item(self, key: str) -> Optional[MemoryItem]:
        item = self._store.get(key)
        if item is None:
            return None
        if item.is_expired():
            del self._store[key]
            return None
        return item

    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    def clear(self) -> None:
        self._store.clear()

    def keys(self) -> list[str]:
        self._clean_expired()
        return list(self._store.keys())

    def search(self, query: str) -> list[MemoryItem]:
        self._clean_expired()
        results: list[MemoryItem] = []
        q = query.lower()
        for item in self._store.values():
            value_str = str(item.value).lower()
            meta_str = str(item.metadata).lower()
            if q in value_str or q in meta_str:
                results.append(item)
        return results

    def _clean_expired(self) -> None:
        expired = [k for k, v in self._store.items() if v.is_expired()]
        for k in expired:
            del self._store[k]

    def __len__(self) -> int:
        self._clean_expired()
        return len(self._store)

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None
