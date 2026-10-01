"""工具注册表与注册装饰器。

提供工具的注册、查找与统一调用接口。
"""

from __future__ import annotations

from typing import Any, Optional, Type

from .base import BaseTool


class ToolRegistry:
    """工具注册表。

    管理所有已注册的工具实例，提供统一的查询与调用入口。
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """注册一个工具实例。"""
        if not tool.name:
            raise ValueError("工具必须定义 name 属性")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """根据名称获取工具，不存在返回 None。"""
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """列出所有已注册工具的名称。"""
        return list(self._tools.keys())

    def get_schemas(self) -> list[dict[str, Any]]:
        """获取所有工具的 schema，供 LLM 调用参考。"""
        return [tool.schema for tool in self._tools.values()]

    def call(self, name: str, **kwargs: Any) -> Any:
        """调用指定工具。

        Args:
            name: 工具名称。
            **kwargs: 传递给工具的参数。

        Returns:
            工具执行结果。

        Raises:
            KeyError: 工具不存在。
        """
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"工具 '{name}' 未注册")
        return tool.run(**kwargs)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)


# 全局默认注册表，供装饰器使用
_default_registry = ToolRegistry()


def register_tool(cls: Type[BaseTool]) -> Type[BaseTool]:
    """工具注册装饰器。

    将工具类注册到默认注册表。被装饰的类必须继承 BaseTool。

    Example:
        @register_tool
        class CalculatorTool(BaseTool):
            name = "calculator"
            ...
    """
    instance = cls()
    _default_registry.register(instance)
    return cls


def get_default_registry() -> ToolRegistry:
    """获取全局默认注册表。"""
    return _default_registry
