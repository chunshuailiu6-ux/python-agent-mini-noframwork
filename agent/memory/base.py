"""记忆系统基类与数据模型。

记忆系统分为两层：
- 短期记忆（ShortTermMemory）：内存存储，会话级别，带 TTL。
- 长期记忆（LongTermMemory）：SQLite 持久化，支持简单搜索。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Optional

from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    """单条记忆。

    Attributes:
        key: 记忆键名。
        value: 记忆内容。
        metadata: 附加元数据（如来源、标签）。
        created_at: 创建时间。
        ttl: 存活时间（秒），None 表示永不过期。
    """

    key: str
    value: Any
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    ttl: Optional[int] = None

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        if self.ttl is None:
            return False
        now = now or datetime.now()
        return now > self.created_at + timedelta(seconds=self.ttl)


class BaseMemory(ABC):
    """记忆系统抽象基类。"""

    @abstractmethod
    def add(self, key: str, value: Any, metadata: Optional[dict] = None, ttl: Optional[int] = None) -> None:
        """添加一条记忆。"""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """根据键获取记忆值，不存在返回 None。"""

    @abstractmethod
    def get_item(self, key: str) -> Optional[MemoryItem]:
        """获取完整记忆条目（含元数据）。"""

    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除指定记忆。"""

    @abstractmethod
    def clear(self) -> None:
        """清空所有记忆。"""

    @abstractmethod
    def keys(self) -> list[str]:
        """获取所有键。"""

    @abstractmethod
    def search(self, query: str) -> list[MemoryItem]:
        """简单搜索：返回 value 或 metadata 中包含 query 的记忆。"""
