"""工具系统单元测试。"""

from __future__ import annotations

import pytest

from agent.tools import (
    BaseTool,
    CalculatorTool,
    FileReadTool,
    FileWriteTool,
    ToolRegistry,
    register_builtin_tools,
    register_tool,
)


class TestToolRegistry:
    def setup_method(self):
        self.reg = ToolRegistry()

    def test_register_and_get(self):
        self.reg.register(CalculatorTool())
        tool = self.reg.get("calculator")
        assert tool is not None
        assert tool.name == "calculator"

    def test_list_tools(self):
        register_builtin_tools(self.reg)
        assert set(self.reg.list_tools()) == {"calculator", "file_read", "file_write", "web_request"}

    def test_call(self):
        self.reg.register(CalculatorTool())
        assert self.reg.call("calculator", expression="2 + 3") == "5"

    def test_call_missing_tool(self):
        with pytest.raises(KeyError):
            self.reg.call("nonexistent")

    def test_contains(self):
        self.reg.register(CalculatorTool())
        assert "calculator" in self.reg
        assert "missing" not in self.reg

    def test_get_schemas(self):
        self.reg.register(CalculatorTool())
        schemas = self.reg.get_schemas()
        assert len(schemas) == 1
        assert schemas[0]["name"] == "calculator"


class TestRegisterToolDecorator:
    def test_decorator_registers(self):
        from agent.tools.registry import _default_registry

        @register_tool
        class DummyTool(BaseTool):
            name = "dummy_test_tool"
            description = "test"

            def run(self, **kwargs):
                return "dummy"

        assert "dummy_test_tool" in _default_registry
        # 清理
        del _default_registry._tools["dummy_test_tool"]


class TestCalculatorTool:
    def setup_method(self):
        self.calc = CalculatorTool()

    def test_addition(self):
        assert self.calc.run(expression="2 + 3") == "5"

    def test_multiplication(self):
        assert self.calc.run(expression="4 * 5") == "20"

    def test_power(self):
        assert self.calc.run(expression="2 ** 3") == "8"

    def test_complex(self):
        assert self.calc.run(expression="(2 + 3) * 4") == "20"

    def test_invalid_expression(self):
        result = self.calc.run(expression="abc + def")
        assert "错误" in result


class TestFileTools:
    def test_write_and_read(self, tmp_path):
        fpath = tmp_path / "test.txt"
        write_tool = FileWriteTool()
        read_tool = FileReadTool()

        result = write_tool.run(path=str(fpath), content="hello world")
        assert "成功" in result

        content = read_tool.run(path=str(fpath))
        assert content == "hello world"

    def test_append(self, tmp_path):
        fpath = tmp_path / "append.txt"
        write_tool = FileWriteTool()
        write_tool.run(path=str(fpath), content="line1")
        write_tool.run(path=str(fpath), content="line2", append=True)
        content = FileReadTool().run(path=str(fpath))
        assert "line1" in content and "line2" in content
