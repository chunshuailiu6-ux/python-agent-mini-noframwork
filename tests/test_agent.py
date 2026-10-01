"""Agent 核心单元测试。"""

from __future__ import annotations

from agent import Agent
from agent.context import ContextScope


class TestAgent:
    def setup_method(self):
        self.agent = Agent("test-agent")

    def test_agent_name(self):
        assert self.agent.name == "test-agent"

    def test_list_tools(self):
        tools = self.agent.list_tools()
        assert "calculator" in tools
        assert "file_read" in tools

    def test_run_calc(self):
        result = self.agent.run("calc 10 + 20")
        assert result == "30"

    def test_run_tools(self):
        result = self.agent.run("tools")
        assert "calculator" in result

    def test_run_remember_recall(self):
        self.agent.run("remember color blue")
        result = self.agent.run("recall color")
        assert "blue" in result

    def test_run_default(self):
        result = self.agent.run("你好")
        assert "收到" in result

    def test_run_empty(self):
        result = self.agent.run("")
        assert "你好" in result

    def test_call_tool_direct(self):
        result = self.agent.call_tool("calculator", expression="7 * 6")
        assert result == "42"

    def test_remember_and_recall_api(self):
        self.agent.remember("key", "value")
        assert self.agent.recall("key") == "value"

    def test_context_api(self):
        self.agent.set_context("lang", "zh", scope=ContextScope.GLOBAL)
        assert self.agent.get_context("lang") == "zh"

    def test_memory_records_inputs(self):
        self.agent.run("first input")
        self.agent.run("second input")
        # 每次 run 会记录一条记忆
        assert len(self.agent.memory) >= 2
