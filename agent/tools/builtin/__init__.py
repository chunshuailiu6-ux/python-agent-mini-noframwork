"""内置工具集。"""

from .calculator import CalculatorTool
from .file_ops import FileReadTool, FileWriteTool
from .web_request import WebRequestTool

__all__ = ["CalculatorTool", "FileReadTool", "FileWriteTool", "WebRequestTool"]


def register_builtin_tools(registry) -> None:
    """将所有内置工具注册到指定注册表。"""
    for tool_cls in [CalculatorTool, FileReadTool, FileWriteTool, WebRequestTool]:
        registry.register(tool_cls())
