"""上下文系统单元测试。

覆盖功能：
- 基本 CRUD（set / get / delete / has）
- 作用域管理（GLOBAL / SESSION / TEMP）
- TTL 过期策略
- 序列化 / 反序列化
- 边界情况
"""

from __future__ import annotations

import time

import pytest

from agent.context import ContextItem, ContextManager, ContextScope


class TestContextScope:
    """作用域枚举测试。"""

    def test_scope_values(self):
        assert ContextScope.GLOBAL.value == "global"
        assert ContextScope.SESSION.value == "session"
        assert ContextScope.TEMP.value == "temp"

    def test_scope_from_string(self):
        assert ContextScope("global") is ContextScope.GLOBAL
        assert ContextScope("session") is ContextScope.SESSION
        assert ContextScope("temp") is ContextScope.TEMP


class TestContextItem:
    """ContextItem 模型测试。"""

    def test_default_scope_is_session(self):
        item = ContextItem(key="k", value="v")
        assert item.scope == ContextScope.SESSION

    def test_no_ttl_never_expires(self):
        item = ContextItem(key="k", value="v", ttl=None)
        assert item.is_expired() is False

    def test_ttl_expires(self):
        item = ContextItem(key="k", value="v", ttl=1)
        # 刚创建未过期
        assert item.is_expired() is False
        # 等待超过 ttl
        time.sleep(1.1)
        assert item.is_expired() is True


class TestContextManagerCRUD:
    """基本增删改查测试。"""

    def setup_method(self):
        self.ctx = ContextManager()

    def test_set_and_get(self):
        self.ctx.set(ContextScope.SESSION, "name", "Alice")
        assert self.ctx.get("name") == "Alice"

    def test_get_missing_returns_default(self):
        assert self.ctx.get("missing") is None
        assert self.ctx.get("missing", default="fallback") == "fallback"

    def test_set_overwrites_value(self):
        self.ctx.set(ContextScope.SESSION, "count", 1)
        assert self.ctx.get("count") == 1
        self.ctx.set(ContextScope.SESSION, "count", 2)
        assert self.ctx.get("count") == 2

    def test_has(self):
        assert self.ctx.has("name") is False
        self.ctx.set(ContextScope.SESSION, "name", "Alice")
        assert self.ctx.has("name") is True

    def test_has_with_none_value(self):
        """value 为 None 时 has 仍应返回 True。"""
        self.ctx.set(ContextScope.SESSION, "flag", None)
        assert self.ctx.has("flag") is True
        assert self.ctx.get("flag") is None

    def test_delete(self):
        self.ctx.set(ContextScope.SESSION, "name", "Alice")
        assert self.ctx.delete("name") is True
        assert self.ctx.has("name") is False

    def test_delete_missing(self):
        assert self.ctx.delete("missing") is False

    def test_keys(self):
        self.ctx.set(ContextScope.SESSION, "a", 1)
        self.ctx.set(ContextScope.SESSION, "b", 2)
        assert set(self.ctx.keys()) == {"a", "b"}

    def test_len(self):
        assert len(self.ctx) == 0
        self.ctx.set(ContextScope.SESSION, "a", 1)
        self.ctx.set(ContextScope.SESSION, "b", 2)
        assert len(self.ctx) == 2

    def test_contains(self):
        self.ctx.set(ContextScope.SESSION, "a", 1)
        assert "a" in self.ctx
        assert "b" not in self.ctx

    def test_value_types(self):
        """支持多种值类型。"""
        self.ctx.set(ContextScope.SESSION, "str", "hello")
        self.ctx.set(ContextScope.SESSION, "int", 42)
        self.ctx.set(ContextScope.SESSION, "float", 3.14)
        self.ctx.set(ContextScope.SESSION, "list", [1, 2, 3])
        self.ctx.set(ContextScope.SESSION, "dict", {"k": "v"})
        self.ctx.set(ContextScope.SESSION, "bool", True)

        assert self.ctx.get("str") == "hello"
        assert self.ctx.get("int") == 42
        assert self.ctx.get("float") == 3.14
        assert self.ctx.get("list") == [1, 2, 3]
        assert self.ctx.get("dict") == {"k": "v"}
        assert self.ctx.get("bool") is True


class TestContextScopeManagement:
    """作用域管理测试。"""

    def setup_method(self):
        self.ctx = ContextManager()

    def test_set_accepts_string_scope(self):
        self.ctx.set("global", "k", "v")
        item = self.ctx.get_item("k")
        assert item.scope == ContextScope.GLOBAL

    def test_get_by_scope(self):
        self.ctx.set(ContextScope.GLOBAL, "g", 1)
        self.ctx.set(ContextScope.SESSION, "s", 2)
        self.ctx.set(ContextScope.TEMP, "t", 3)

        assert self.ctx.get_by_scope("global") == {"g": 1}
        assert self.ctx.get_by_scope(ContextScope.SESSION) == {"s": 2}
        assert self.ctx.get_by_scope(ContextScope.TEMP) == {"t": 3}

    def test_clear_all(self):
        self.ctx.set(ContextScope.GLOBAL, "g", 1)
        self.ctx.set(ContextScope.SESSION, "s", 2)
        self.ctx.clear()
        assert len(self.ctx) == 0

    def test_clear_by_scope(self):
        self.ctx.set(ContextScope.GLOBAL, "g", 1)
        self.ctx.set(ContextScope.SESSION, "s", 2)
        self.ctx.clear(ContextScope.SESSION)
        assert self.ctx.has("g") is True
        assert self.ctx.has("s") is False


class TestContextTTL:
    """TTL 过期策略测试。"""

    def setup_method(self):
        self.ctx = ContextManager()

    def test_ttl_expires_on_get(self):
        self.ctx.set(ContextScope.SESSION, "k", "v", ttl=1)
        assert self.ctx.get("k") == "v"
        time.sleep(1.1)
        # 过期后 get 应返回默认值并自动清理
        assert self.ctx.get("k") is None
        assert self.ctx.has("k") is False

    def test_ttl_expires_on_keys(self):
        self.ctx.set(ContextScope.SESSION, "k", "v", ttl=1)
        time.sleep(1.1)
        assert "k" not in self.ctx.keys()

    def test_no_ttl_persists(self):
        self.ctx.set(ContextScope.SESSION, "k", "v", ttl=None)
        time.sleep(0.2)
        assert self.ctx.get("k") == "v"

    def test_update_ttl_on_overwrite(self):
        self.ctx.set(ContextScope.SESSION, "k", "v", ttl=1)
        time.sleep(0.5)
        # 重新设置更长的 ttl
        self.ctx.set(ContextScope.SESSION, "k", "v2", ttl=10)
        time.sleep(0.7)
        # 原 ttl 已过，但新 ttl 未过，应仍有效
        assert self.ctx.get("k") == "v2"


class TestContextSerialization:
    """序列化 / 反序列化测试。"""

    def setup_method(self):
        self.ctx = ContextManager()

    def test_serialize_deserialize_roundtrip(self):
        self.ctx.set(ContextScope.GLOBAL, "g", "global_val")
        self.ctx.set(ContextScope.SESSION, "s", 123)
        self.ctx.set(ContextScope.TEMP, "t", [1, 2, 3])

        data = self.ctx.serialize()
        assert isinstance(data, str)

        # 反序列化到新的 ContextManager
        ctx2 = ContextManager()
        ctx2.deserialize(data)

        assert ctx2.get("g") == "global_val"
        assert ctx2.get("s") == 123
        assert ctx2.get("t") == [1, 2, 3]

    def test_deserialize_overwrites_existing(self):
        self.ctx.set(ContextScope.SESSION, "old", "old_val")
        data = self.ctx.serialize()

        ctx2 = ContextManager()
        ctx2.set(ContextScope.SESSION, "new", "new_val")
        ctx2.deserialize(data)

        assert ctx2.has("old") is True
        assert ctx2.has("new") is False

    def test_serialize_skips_expired(self):
        self.ctx.set(ContextScope.SESSION, "k", "v", ttl=1)
        time.sleep(1.1)
        data = self.ctx.serialize()
        # 反序列化后不应有过期条目
        ctx2 = ContextManager()
        ctx2.deserialize(data)
        assert ctx2.has("k") is False

    def test_to_dict(self):
        self.ctx.set(ContextScope.SESSION, "a", 1)
        self.ctx.set(ContextScope.SESSION, "b", 2)
        assert self.ctx.to_dict() == {"a": 1, "b": 2}


class TestContextGetItem:
    """get_item 元数据测试。"""

    def setup_method(self):
        self.ctx = ContextManager()

    def test_get_item_returns_metadata(self):
        self.ctx.set(ContextScope.SESSION, "k", "v", ttl=60)
        item = self.ctx.get_item("k")
        assert item is not None
        assert item.key == "k"
        assert item.value == "v"
        assert item.scope == ContextScope.SESSION
        assert item.ttl == 60
        assert item.created_at is not None
        assert item.updated_at is not None

    def test_get_item_missing(self):
        assert self.ctx.get_item("missing") is None

    def test_update_preserves_created_at(self):
        self.ctx.set(ContextScope.SESSION, "k", "v1")
        item1 = self.ctx.get_item("k")
        time.sleep(0.05)
        self.ctx.set(ContextScope.SESSION, "k", "v2")
        item2 = self.ctx.get_item("k")
        # created_at 不变，updated_at 更新
        assert item1.created_at == item2.created_at
        assert item2.updated_at >= item1.updated_at
