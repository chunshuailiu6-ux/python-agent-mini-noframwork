"""长期记忆：基于 SQLite 的持久化存储。

使用 Python 标准库 sqlite3，无需额外依赖。
value 和 metadata 以 JSON 字符串形式存储。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .base import BaseMemory, MemoryItem


class LongTermMemory(BaseMemory):
    """长期记忆，使用 SQLite 持久化。

    特点：
    - 数据持久化到本地文件，重启不丢失。
    - 支持简单的 LIKE 搜索。
    - value / metadata 以 JSON 序列化存储。
    """

    def __init__(self, db_path: str = "./data/memory.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_table()

    def _init_table(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                ttl INTEGER
            )
            """
        )
        self._conn.commit()

    def add(self, key: str, value: Any, metadata: Optional[dict] = None, ttl: Optional[int] = None) -> None:
        value_json = json.dumps(value, ensure_ascii=False, default=str)
        meta_json = json.dumps(metadata or {}, ensure_ascii=False, default=str)
        created_at = datetime.now().isoformat()
        self._conn.execute(
            """
            INSERT OR REPLACE INTO memories (key, value, metadata, created_at, ttl)
            VALUES (?, ?, ?, ?, ?)
            """,
            (key, value_json, meta_json, created_at, ttl),
        )
        self._conn.commit()

    def get(self, key: str) -> Optional[Any]:
        item = self.get_item(key)
        return item.value if item else None

    def get_item(self, key: str) -> Optional[MemoryItem]:
        row = self._conn.execute(
            "SELECT * FROM memories WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_item(row)

    def delete(self, key: str) -> bool:
        cursor = self._conn.execute("DELETE FROM memories WHERE key = ?", (key,))
        self._conn.commit()
        return cursor.rowcount > 0

    def clear(self) -> None:
        self._conn.execute("DELETE FROM memories")
        self._conn.commit()

    def keys(self) -> list[str]:
        rows = self._conn.execute("SELECT key FROM memories").fetchall()
        return [row["key"] for row in rows]

    def search(self, query: str) -> list[MemoryItem]:
        like = f"%{query}%"
        rows = self._conn.execute(
            "SELECT * FROM memories WHERE value LIKE ? OR metadata LIKE ?",
            (like, like),
        ).fetchall()
        return [self._row_to_item(row) for row in rows]

    def _row_to_item(self, row: sqlite3.Row) -> MemoryItem:
        return MemoryItem(
            key=row["key"],
            value=json.loads(row["value"]),
            metadata=json.loads(row["metadata"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            ttl=row["ttl"],
        )

    def close(self) -> None:
        """关闭数据库连接。"""
        self._conn.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
