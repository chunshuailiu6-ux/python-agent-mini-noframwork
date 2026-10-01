"""网络请求工具：发送 HTTP GET 请求。"""

from __future__ import annotations

from typing import Any

import httpx

from ..base import BaseTool


class WebRequestTool(BaseTool):
    """发送 HTTP GET 请求并返回响应内容。"""

    name = "web_request"
    description = "发送 HTTP GET 请求，返回响应文本"
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "请求的 URL"},
            "timeout": {"type": "number", "description": "超时时间（秒），默认 10", "default": 10},
        },
        "required": ["url"],
    }

    def run(self, url: str, timeout: float = 10.0, **kwargs: Any) -> str:
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.get(url)
                return f"HTTP {resp.status_code}\n{resp.text[:2000]}"
        except Exception as e:
            return f"请求失败: {e}"
