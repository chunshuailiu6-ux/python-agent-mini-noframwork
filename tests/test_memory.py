"""记忆系统单元测试。"""

from __future__ import annotations

import time

from agent.memory import LongTermMemory, ShortTermMemory


class TestShortTermMemory:
    def setup_method(self):
        self.mem = ShortTermMemory()

    def test_add_and_get(self):
        self.mem.add("k", "v")
        assert self.mem.get("k") == "v"

    def test_get_missing(self):
        assert self.mem.get("missing") is None

    def test_delete(self):
        self.mem.add("k", "v")
        assert self.mem.delete("k") is True
        assert self.mem.get("k") is None

    def test_delete_missing(self):
        assert self.mem.delete("missing") is False

    def test_clear(self):
        self.mem.add("a", 1)
        self.mem.add("b", 2)
        self.mem.clear()
        assert len(self.mem) == 0

    def test_keys(self):
        self.mem.add("a", 1)
        self.mem.add("b", 2)
        assert set(self.mem.keys()) == {"a", "b"}

    def test_search(self):
        self.mem.add("greeting", "hello world", metadata={"tag": "en"})
        self.mem.add("farewell", "goodbye", metadata={"tag": "en"})
        results = self.mem.search("hello")
        assert len(results) == 1
        assert results[0].key == "greeting"

    def test_ttl_expires(self):
        self.mem.add("k", "v", ttl=1)
        assert self.mem.get("k") == "v"
        time.sleep(1.1)
        assert self.mem.get("k") is None

    def test_metadata(self):
        self.mem.add("k", "v", metadata={"src": "test"})
        item = self.mem.get_item("k")
        assert item.metadata == {"src": "test"}

    def test_contains(self):
        self.mem.add("k", "v")
        assert "k" in self.mem
        assert "x" not in self.mem


class TestLongTermMemory:
    def _make(self, tmp_path):
        return LongTermMemory(str(tmp_path / "test_mem.db"))

    def test_add_and_get(self, tmp_path):
        mem = self._make(tmp_path)
        mem.add("k", "v")
        assert mem.get("k") == "v"
        mem.close()

    def test_complex_value(self, tmp_path):
        mem = self._make(tmp_path)
        data = {"name": "Alice", "scores": [90, 85, 95]}
        mem.add("user", data)
        assert mem.get("user") == data
        mem.close()

    def test_delete(self, tmp_path):
        mem = self._make(tmp_path)
        mem.add("k", "v")
        assert mem.delete("k") is True
        assert mem.get("k") is None
        mem.close()

    def test_keys(self, tmp_path):
        mem = self._make(tmp_path)
        mem.add("a", 1)
        mem.add("b", 2)
        assert set(mem.keys()) == {"a", "b"}
        mem.close()

    def test_search(self, tmp_path):
        mem = self._make(tmp_path)
        mem.add("k1", "hello world")
        mem.add("k2", "goodbye")
        results = mem.search("hello")
        assert len(results) == 1
        assert results[0].key == "k1"
        mem.close()

    def test_persistence(self, tmp_path):
        db_path = str(tmp_path / "persist.db")
        mem = LongTermMemory(db_path)
        mem.add("k", "persistent")
        mem.close()
        mem2 = LongTermMemory(db_path)
        assert mem2.get("k") == "persistent"
        mem2.close()

    def test_clear(self, tmp_path):
        mem = self._make(tmp_path)
        mem.add("a", 1)
        mem.clear()
        assert len(mem.keys()) == 0
        mem.close()
