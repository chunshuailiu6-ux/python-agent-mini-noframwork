"""文件操作工具：读取与写入文件。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..base import BaseTool


class FileReadTool(BaseTool):
    """读取文件内容。"""

    name = "file_read"
    description = "读取指定路径的文本文件内容"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "encoding": {"type": "string", "description": "文件编码，默认 utf-8", "default": "utf-8"},
        },
        "required": ["path"],
    }

    def run(self, path: str, encoding: str = "utf-8", **kwargs: Any) -> str:
        try:
            return Path(path).read_text(encoding=encoding)
        except Exception as e:
            return f"读取失败: {e}"


class FileWriteTool(BaseTool):
    """写入文件内容。"""

    name = "file_write"
    description = "将内容写入指定路径的文件"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "content": {"type": "string", "description": "要写入的内容"},
            "append": {"type": "boolean", "description": "是否追加模式，默认 False", "default": False},
            "encoding": {"type": "string", "description": "文件编码，默认 utf-8", "default": "utf-8"},
        },
        "required": ["path", "content"],
    }

    def run(self, path: str, content: str, append: bool = False, encoding: str = "utf-8", **kwargs: Any) -> str:
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            mode = "a" if append else "w"
            with open(p, mode, encoding=encoding) as f:
                f.write(content)
            return f"写入成功: {path}"
        except Exception as e:
            return f"写入失败: {e}"
