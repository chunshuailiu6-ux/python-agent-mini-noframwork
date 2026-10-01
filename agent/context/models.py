"""上下文系统的数据模型定义。

使用 Pydantic 定义上下文数据结构，提供类型安全与自动校验。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ContextScope(str, Enum):
    """上下文作用域。

    - GLOBAL: 全局作用域，在所有会话间共享。
    - SESSION: 会话作用域，仅在当前会话内有效。
    - TEMP: 临时作用域，通常用于单次请求，用完即弃。
    """

    GLOBAL = "global"
    SESSION = "session"
    TEMP = "temp"


class ContextItem(BaseModel):
    """单个上下文条目。

    Attributes:
        key: 上下文键名，唯一标识。
        value: 上下文值，可以是任意可序列化类型。
        scope: 作用域，默认为 SESSION。
        created_at: 创建时间。
        updated_at: 最后更新时间。
        ttl: 存活时间（秒），None 表示永不过期。
    """

    key: str
    value: Any
    scope: ContextScope = ContextScope.SESSION
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    ttl: Optional[int] = None

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        """判断该条目是否已过期。

        Args:
            now: 当前时间，默认使用 datetime.now()。

        Returns:
            True 表示已过期，False 表示未过期或无 TTL。
        """
        if self.ttl is None:
            return False
        now = now or datetime.now()
        expire_at = self.created_at + timedelta(seconds=self.ttl)
        return now > expire_at


class ContextSnapshot(BaseModel):
    """上下文快照，用于序列化与持久化。

    Attributes:
        items: 所有上下文条目的字典，键为 key。
        created_at: 快照创建时间。
    """

    items: dict[str, ContextItem] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
