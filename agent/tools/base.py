"""工具基类定义。

所有工具需继承 BaseTool 并实现 run 方法。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """工具基类。

    Attributes:
        name: 工具唯一名称。
        description: 工具功能描述。
        parameters: 参数 schema（JSON Schema 风格），供 LLM 理解如何调用。
    """

    name: str = ""
    description: str = ""
    parameters: dict[str, Any] = {}

    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        """执行工具逻辑。

        Args:
            **kwargs: 工具参数。

        Returns:
            工具执行结果。
        """

    @property
    def schema(self) -> dict[str, Any]:
        """返回工具的描述性 schema，用于注册展示。"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    def __repr__(self) -> str:
        return f"<Tool {self.name}>"
