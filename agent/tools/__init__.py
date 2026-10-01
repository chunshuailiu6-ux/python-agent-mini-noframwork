"""工具系统。

提供工具注册、查找与统一调用机制，以及内置基础工具。

核心类：
    - BaseTool: 工具基类。
    - ToolRegistry: 工具注册表。
    - register_tool: 工具注册装饰器。

内置工具：
    - CalculatorTool: 数学计算器。
    - FileReadTool / FileWriteTool: 文件读写。
    - WebRequestTool: HTTP GET 请求。
"""

from .base import BaseTool
from .builtin import CalculatorTool, FileReadTool, FileWriteTool, WebRequestTool, register_builtin_tools
from .registry import ToolRegistry, get_default_registry, register_tool

__all__ = [
    "BaseTool",
    "ToolRegistry",
    "register_tool",
    "get_default_registry",
    "CalculatorTool",
    "FileReadTool",
    "FileWriteTool",
    "WebRequestTool",
    "register_builtin_tools",
]
