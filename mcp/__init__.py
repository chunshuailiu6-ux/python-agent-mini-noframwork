"""多代理协作模块（MCP）。

提供基于 ZeroMQ + JSON-RPC 的多代理通信能力。

核心类：
    - MCPServer / MCPClient: ZeroMQ 传输层。
    - AgentRegistry: 代理注册与发现中心。
    - AgentWorker: 代理工作节点，接收远程调用。
"""

from .protocol import build_request, build_response, is_request, is_response, parse_message
from .registry import AgentInfo, AgentRegistry
from .transport import MCPClient, MCPServer
from .worker import AgentWorker

__all__ = [
    "MCPServer",
    "MCPClient",
    "AgentRegistry",
    "AgentInfo",
    "AgentWorker",
    "build_request",
    "build_response",
    "parse_message",
    "is_request",
    "is_response",
]
