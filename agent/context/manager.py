"""上下文管理器核心实现。

提供上下文的增删改查、作用域管理、TTL 过期策略以及序列化/反序列化能力。
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from .models import ContextItem, ContextScope, ContextSnapshot


class ContextManager:
    """上下文管理器。

    负责管理代理运行过程中的所有上下文数据，支持三种作用域：
    GLOBAL（全局）、SESSION（会话）、TEMP（临时）。
    支持 TTL 过期策略，可序列化为 JSON 字符串以便持久化。

    Example:
        >>> ctx = ContextManager()
        >>> ctx.set(ContextScope.SESSION, "user", "Alice")
        >>> ctx.get("user")
        'Alice'
    """

    def __init__(self) -> None:
        # 内部存储：key -> ContextItem
        self._store: dict[str, ContextItem] = {}

    # ------------------------------------------------------------------
    # 增 / 改
    # ------------------------------------------------------------------
    def set(
        self,
        scope: ContextScope | str,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """设置（创建或更新）一个上下文条目。

        Args:
            scope: 作用域，可以是 ContextScope 枚举或其字符串值。
            key: 键名。
            value: 值，可以是任意可 JSON 序列化的类型。
            ttl: 存活时间（秒），None 表示永不过期。
        """
        scope = self._normalize_scope(scope)
        now = datetime.now()

        if key in self._store:
            # 更新已有条目：保留 created_at，更新 value/scope/ttl/updated_at
            item = self._store[key]
            item.value = value
            item.scope = scope
            item.ttl = ttl
            item.updated_at = now
        else:
            # 新建条目
            self._store[key] = ContextItem(
                key=key,
                value=value,
                scope=scope,
                created_at=now,
                updated_at=now,
                ttl=ttl,
            )

    # ------------------------------------------------------------------
    # 查
    # ------------------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文值。

        如果条目已过期，会自动删除并返回 default。

        Args:
            key: 键名。
            default: 键不存在或已过期时的返回值。

        Returns:
            上下文值，或 default。
        """
        item = self._store.get(key)
        if item is None:
            return default
        if item.is_expired():
            del self._store[key]
            return default
        return item.value

    def get_item(self, key: str) -> Optional[ContextItem]:
        """获取完整的 ContextItem 对象（含元数据）。

        与 get() 不同，此方法返回包含 created_at、ttl 等元数据的完整对象。
        过期条目同样会被自动清理。

        Args:
            key: 键名。

        Returns:
            ContextItem 对象，或 None。
        """
        item = self._store.get(key)
        if item is None:
            return None
        if item.is_expired():
            del self._store[key]
            return None
        return item

    def get_by_scope(self, scope: ContextScope | str) -> dict[str, Any]:
        """获取指定作用域下的所有键值对。

        过期条目会被自动过滤。

        Args:
            scope: 作用域。

        Returns:
            该作用域下的 {key: value} 字典。
        """
        scope = self._normalize_scope(scope)
        result: dict[str, Any] = {}
        expired_keys: list[str] = []
        for key, item in self._store.items():
            if item.scope == scope:
                if item.is_expired():
                    expired_keys.append(key)
                else:
                    result[key] = item.value
        # 清理过期条目
        for key in expired_keys:
            del self._store[key]
        return result

    def has(self, key: str) -> bool:
        """判断键是否存在且未过期。"""
        item = self._store.get(key)
        if item is None:
            return False
        if item.is_expired():
            del self._store[key]
            return False
        return True

    def keys(self) -> list[str]:
        """获取所有未过期键的列表。"""
        self._clean_expired()
        return list(self._store.keys())

    def items(self) -> dict[str, Any]:
        """获取所有未过期的 {key: value} 字典。"""
        self._clean_expired()
        return {k: v.value for k, v in self._store.items()}

    # ------------------------------------------------------------------
    # 删
    # ------------------------------------------------------------------
    def delete(self, key: str) -> bool:
        """删除指定键。

        Args:
            key: 键名。

        Returns:
            True 表示删除成功，False 表示键不存在。
        """
        if key in self._store:
            del self._store[key]
            return True
        return False

    def clear(self, scope: Optional[ContextScope | str] = None) -> None:
        """清空上下文。

        Args:
            scope: 指定作用域时仅清空该作用域；为 None 时清空全部。
        """
        if scope is None:
            self._store.clear()
            return
        scope = self._normalize_scope(scope)
        self._store = {
            k: v for k, v in self._store.items() if v.scope != scope
        }

    # ------------------------------------------------------------------
    # 序列化 / 反序列化
    # ------------------------------------------------------------------
    def serialize(self) -> str:
        """将当前上下文序列化为 JSON 字符串。

        Returns:
            JSON 格式的字符串。
        """
        self._clean_expired()
        snapshot = ContextSnapshot(items=dict(self._store))
        return snapshot.model_dump_json()

    def deserialize(self, data: str) -> None:
        """从 JSON 字符串反序列化并覆盖当前上下文。

        Args:
            data: serialize() 生成的 JSON 字符串。
        """
        snapshot = ContextSnapshot.model_validate_json(data)
        self._store = dict(snapshot.items)
        self._clean_expired()

    def to_dict(self) -> dict[str, Any]:
        """导出为普通字典（不含元数据），便于调试。"""
        self._clean_expired()
        return {k: v.value for k, v in self._store.items()}

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_scope(scope: ContextScope | str) -> ContextScope:
        """将字符串作用域规范化为 ContextScope 枚举。"""
        if isinstance(scope, ContextScope):
            return scope
        return ContextScope(scope)

    def _clean_expired(self) -> None:
        """清理所有已过期的条目。"""
        expired = [k for k, v in self._store.items() if v.is_expired()]
        for key in expired:
            del self._store[key]

    def __len__(self) -> int:
        """返回未过期条目数量。"""
        self._clean_expired()
        return len(self._store)

    def __contains__(self, key: str) -> bool:
        """支持 `key in ctx` 语法。"""
        return self.has(key)

    def __repr__(self) -> str:
        return f"ContextManager(keys={self.keys()})"
