"""JSON-RPC 2.0 协议实现。

提供请求与响应消息的构建与解析。
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional


def build_request(method: str, params: Optional[dict] = None, request_id: Optional[str] = None) -> str:
    """构建 JSON-RPC 请求消息。

    Args:
        method: 方法名。
        params: 参数。
        request_id: 请求 ID，默认自动生成。

    Returns:
        JSON 字符串。
    """
    msg = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": request_id or uuid.uuid4().hex[:8],
    }
    return json.dumps(msg, ensure_ascii=False)


def build_response(request_id: str, result: Any = None, error: Optional[dict] = None) -> str:
    """构建 JSON-RPC 响应消息。

    Args:
        request_id: 对应的请求 ID。
        result: 成功结果。
        error: 错误信息（code, message）。

    Returns:
        JSON 字符串。
    """
    msg = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    return json.dumps(msg, ensure_ascii=False)


def parse_message(data: str) -> dict:
    """解析 JSON-RPC 消息。

    Args:
        data: JSON 字符串。

    Returns:
        消息字典。

    Raises:
        ValueError: JSON 解析失败。
    """
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"无效的 JSON-RPC 消息: {e}")


def is_request(msg: dict) -> bool:
    """判断是否为请求消息。"""
    return "method" in msg and "id" in msg


def is_response(msg: dict) -> bool:
    """判断是否为响应消息。"""
    return "result" in msg or "error" in msg
