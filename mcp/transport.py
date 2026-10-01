"""ZeroMQ 消息传输层。

提供基于 REQ/REP 模式的服务端与客户端。
"""

from __future__ import annotations

from typing import Callable, Optional

import zmq

from .protocol import build_response, parse_message


class MCPServer:
    """MCP 服务端（REP 模式）。

    接收请求，调用处理函数，返回响应。

    Args:
        address: 监听地址，如 "tcp://127.0.0.1:5555"。
        handler: 请求处理函数，接收解析后的消息字典，返回结果。
    """

    def __init__(self, address: str, handler: Callable[[dict], dict]) -> None:
        self.address = address
        self._handler = handler
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REP)
        self._socket.bind(address)

    def serve_once(self, timeout_ms: int = 1000) -> Optional[dict]:
        """处理一次请求（非阻塞，带超时）。

        Args:
            timeout_ms: 超时毫秒数。

        Returns:
            处理后的响应消息字典，或 None（超时无请求）。
        """
        poller = zmq.Poller()
        poller.register(self._socket, zmq.POLLIN)
        events = dict(poller.poll(timeout_ms))
        if self._socket not in events:
            return None

        raw = self._socket.recv_string()
        msg = parse_message(raw)
        try:
            result = self._handler(msg)
            response = build_response(msg["id"], result=result)
        except Exception as e:
            response = build_response(msg["id"], error={"code": -1, "message": str(e)})
        self._socket.send_string(response)
        return parse_message(response)

    def close(self) -> None:
        self._socket.close()
        self._context.term()


class MCPClient:
    """MCP 客户端（REQ 模式）。

    发送请求并等待响应。

    Args:
        address: 服务端地址，如 "tcp://127.0.0.1:5555"。
    """

    def __init__(self, address: str) -> None:
        self.address = address
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REQ)
        self._socket.connect(address)

    def call(self, method: str, params: Optional[dict] = None, timeout_ms: int = 5000) -> dict:
        """调用远程方法。

        Args:
            method: 方法名。
            params: 参数。
            timeout_ms: 超时毫秒数。

        Returns:
            响应消息字典。

        Raises:
            TimeoutError: 等待响应超时。
        """
        from .protocol import build_request

        request = build_request(method, params)
        self._socket.send_string(request)

        poller = zmq.Poller()
        poller.register(self._socket, zmq.POLLIN)
        events = dict(poller.poll(timeout_ms))
        if self._socket not in events:
            raise TimeoutError(f"调用 {method} 超时")

        raw = self._socket.recv_string()
        return parse_message(raw)

    def close(self) -> None:
        self._socket.close()
        self._context.term()
