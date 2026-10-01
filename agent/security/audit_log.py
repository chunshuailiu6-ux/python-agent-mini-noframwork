"""操作审计日志。

将敏感操作记录到 SQLite，便于追溯。
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class AuditLog:
    """操作审计日志，基于 SQLite 持久化。"""

    def __init__(self, db_path: str = "./data/audit.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_table()

    def _init_table(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                role TEXT NOT NULL,
                action TEXT NOT NULL,
                target TEXT,
                detail TEXT,
                allowed INTEGER NOT NULL
            )
            """
        )
        self._conn.commit()

    def log(
        self,
        role: str,
        action: str,
        target: Optional[str] = None,
        detail: Optional[str] = None,
        allowed: bool = True,
    ) -> None:
        """记录一条审计日志。

        Args:
            role: 执行操作的角色。
            action: 操作类型（如 tool_call）。
            target: 操作目标（如工具名）。
            detail: 详细信息。
            allowed: 是否被允许。
        """
        self._conn.execute(
            """
            INSERT INTO audit_logs (timestamp, role, action, target, detail, allowed)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(),
                role,
                action,
                target,
                detail,
                1 if allowed else 0,
            ),
        )
        self._conn.commit()

    def query(self, limit: int = 100) -> list[dict[str, Any]]:
        """查询最近的审计日志。"""
        rows = self._conn.execute(
            "SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]

    def clear(self) -> None:
        """清空所有审计日志。"""
        self._conn.execute("DELETE FROM audit_logs")
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
