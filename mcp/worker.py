"""代理工作节点。

运行在每个代理实例上，通过 ZeroMQ 接收远程调用，
将请求分发到代理的方法执行。
"""

from __future__ import annotations

from typing import Any, Optional

from agent.core.base_agent import Agent

from .registry import AgentRegistry
from .transport import MCPServer


class AgentWorker:
    """代理工作节点。

    将 Agent 暴露为 MCP 服务，接收远程方法调用。

    Args:
        agent: 代理实例。
        address: 监听地址。
        registry: 注册中心（可选，用于注册自身）。
    """

    def __init__(
        self,
        agent: Agent,
        address: str = "tcp://127.0.0.1:5555",
        registry: Optional[AgentRegistry] = None,
    ) -> None:
        self.agent = agent
        self.address = address
        self.registry = registry
        self._server: Optional[MCPServer] = None
        self._registered = False

    def start(self) -> None:
        """启动工作节点并注册到注册中心。"""
        self._server = MCPServer(self.address, self._handle_request)
        if self.registry is not None:
            self.registry.register(
                agent_id=self.agent.name,
                name=self.agent.name,
                address=self.address,
                capabilities=self.agent.list_tools(),
            )
            self._registered = True

    def serve_once(self, timeout_ms: int = 1000) -> Optional[dict]:
        """处理一次请求。"""
        if self._server is None:
            raise RuntimeError("工作节点未启动，请先调用 start()")
        if self.registry is not None:
            self.registry.heartbeat(self.agent.name)
        return self._server.serve_once(timeout_ms)

    def stop(self) -> None:
        """停止工作节点。"""
        if self.registry is not None and self._registered:
            self.registry.unregister(self.agent.name)
            self._registered = False
        if self._server is not None:
            self._server.close()
            self._server = None

    def _handle_request(self, msg: dict) -> Any:
        """处理远程请求，分发到代理方法。

        支持的方法：
        - run: 代理.run(user_input)
        - call_tool: 代理.call_tool(name, **params)
        - list_tools: 代理.list_tools()
        - remember: 代理.remember(key, value)
        - recall: 代理.recall(key)
        """
        method = msg.get("method", "")
        params = msg.get("params", {})

        if method == "run":
            return self.agent.run(params.get("input", ""))
        if method == "call_tool":
            tool_name = params.pop("name", "")
            return self.agent.call_tool(tool_name, **params)
        if method == "list_tools":
            return self.agent.list_tools()
        if method == "remember":
            self.agent.remember(params["key"], params["value"])
            return "ok"
        if method == "recall":
            return self.agent.recall(params["key"])
        raise ValueError(f"未知方法: {method}")
