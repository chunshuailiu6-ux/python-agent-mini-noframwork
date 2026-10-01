"""基础代理类。

Agent 是系统的核心，组合了上下文（Context）、记忆（Memory）和工具（Tools），
对外提供统一的 run 接口。

本实现不依赖 LLM，采用基于规则的简单处理逻辑，
后续可扩展接入大语言模型。
"""

from __future__ import annotations

import re
from typing import Any, Optional

from agent.context import ContextManager, ContextScope
from agent.memory import ShortTermMemory
from agent.tools import ToolRegistry, register_builtin_tools


class Agent:
    """基础智能代理。

    组合上下文管理、短期记忆与工具系统，提供统一的交互入口。

    Args:
        name: 代理名称。
        context: 上下文管理器，默认新建。
        memory: 短期记忆，默认新建。
        tools: 工具注册表，默认新建并注册内置工具。
    """

    def __init__(
        self,
        name: str = "mini-agent",
        context: Optional[ContextManager] = None,
        memory: Optional[ShortTermMemory] = None,
        tools: Optional[ToolRegistry] = None,
    ) -> None:
        self.name = name
        self.context = context or ContextManager()
        self.memory = memory or ShortTermMemory()
        self.tools = tools or ToolRegistry()
        if self.tools is not None and len(self.tools) == 0:
            register_builtin_tools(self.tools)

        # 记录对话历史到上下文
        self.context.set(ContextScope.SESSION, "agent_name", name)

    # ------------------------------------------------------------------
    # 核心交互
    # ------------------------------------------------------------------
    def run(self, user_input: str) -> str:
        """处理用户输入并返回响应。

        支持的命令格式：
        - "calc <表达式>" -> 调用计算器
        - "read <文件路径>" -> 读取文件
        - "write <路径> <内容>" -> 写入文件
        - "remember <key> <value>" -> 记忆
        - "recall <key>" -> 回忆
        - "tools" -> 列出可用工具
        - 其他 -> 默认响应

        Args:
            user_input: 用户输入文本。

        Returns:
            代理响应文本。
        """
        # 记录用户输入到记忆
        self.memory.add(f"input_{len(self.memory)}", user_input)

        # 去除首尾空白
        text = user_input.strip()

        # 工具命令匹配
        response = self._try_tool_command(text)
        if response is not None:
            return response

        # 记忆命令
        response = self._try_memory_command(text)
        if response is not None:
            return response

        # 默认响应
        return self._default_response(text)

    # ------------------------------------------------------------------
    # 工具调用
    # ------------------------------------------------------------------
    def call_tool(self, name: str, **kwargs: Any) -> Any:
        """直接调用指定工具。"""
        return self.tools.call(name, **kwargs)

    def list_tools(self) -> list[str]:
        """列出所有可用工具。"""
        return self.tools.list_tools()

    def _try_tool_command(self, text: str) -> Optional[str]:
        """尝试将输入解析为工具命令。"""
        # calc <表达式>
        m = re.match(r"^calc\s+(.+)$", text, re.IGNORECASE)
        if m:
            return self.call_tool("calculator", expression=m.group(1))

        # read <路径>
        m = re.match(r"^read\s+(.+)$", text, re.IGNORECASE)
        if m:
            return self.call_tool("file_read", path=m.group(1).strip())

        # write <路径> <内容>
        m = re.match(r"^write\s+(\S+)\s+(.+)$", text, re.IGNORECASE)
        if m:
            return self.call_tool("file_write", path=m.group(1), content=m.group(2))

        # tools
        if text.lower() == "tools":
            return "可用工具: " + ", ".join(self.list_tools())

        return None

    # ------------------------------------------------------------------
    # 记忆操作
    # ------------------------------------------------------------------
    def _try_memory_command(self, text: str) -> Optional[str]:
        """尝试将输入解析为记忆命令。"""
        # remember <key> <value>
        m = re.match(r"^remember\s+(\S+)\s+(.+)$", text, re.IGNORECASE)
        if m:
            key, value = m.group(1), m.group(2)
            self.memory.add(key, value)
            return f"已记忆: {key} = {value}"

        # recall <key>
        m = re.match(r"^recall\s+(\S+)$", text, re.IGNORECASE)
        if m:
            key = m.group(1)
            value = self.memory.get(key)
            if value is None:
                return f"未找到记忆: {key}"
            return f"{key} = {value}"

        return None

    def remember(self, key: str, value: Any, metadata: Optional[dict] = None, ttl: Optional[int] = None) -> None:
        """保存一条记忆。"""
        self.memory.add(key, value, metadata=metadata, ttl=ttl)

    def recall(self, key: str) -> Optional[Any]:
        """回忆一条记忆。"""
        return self.memory.get(key)

    # ------------------------------------------------------------------
    # 上下文操作
    # ------------------------------------------------------------------
    def set_context(self, key: str, value: Any, scope: ContextScope = ContextScope.SESSION) -> None:
        """设置上下文。"""
        self.context.set(scope, key, value)

    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文。"""
        return self.context.get(key, default=default)

    # ------------------------------------------------------------------
    # 默认响应
    # ------------------------------------------------------------------
    def _default_response(self, text: str) -> str:
        """默认响应：回显并提示可用命令。"""
        if not text:
            return "你好，我是 mini-agent。输入 'tools' 查看可用工具。"
        return (
            f"收到: {text}\n"
            f"提示：可用命令包括 calc/read/write/remember/recall/tools"
        )

    def __repr__(self) -> str:
        return f"Agent(name={self.name!r}, tools={len(self.tools)})"
