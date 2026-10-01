"""权限检查中间件。

在工具调用前校验角色权限，并记录审计日志。
"""

from __future__ import annotations

from typing import Any, Optional

from agent.tools import ToolRegistry

from .audit_log import AuditLog
from .rbac import Role, can_use_tool


class SecurityError(Exception):
    """权限不足异常。"""

    def __init__(self, role: Role, tool_name: str) -> None:
        self.role = role
        self.tool_name = tool_name
        super().__init__(f"角色 '{role.value}' 无权使用工具 '{tool_name}'")


class SecurityMiddleware:
    """安全权限中间件。

    包装工具调用，在执行前进行权限检查，并记录审计日志。

    Args:
        registry: 工具注册表。
        audit_log: 审计日志实例，默认新建。
        default_role: 默认角色，默认为 USER。
    """

    def __init__(
        self,
        registry: ToolRegistry,
        audit_log: Optional[AuditLog] = None,
        default_role: Role = Role.USER,
    ) -> None:
        self._registry = registry
        self._audit = audit_log or AuditLog()
        self._default_role = default_role

    def call(self, tool_name: str, role: Optional[Role] = None, **kwargs: Any) -> Any:
        """带权限检查的工具调用。

        Args:
            tool_name: 工具名称。
            role: 调用者角色，默认使用 default_role。
            **kwargs: 工具参数。

        Returns:
            工具执行结果。

        Raises:
            SecurityError: 角色无权使用该工具。
            KeyError: 工具不存在。
        """
        role = role or self._default_role

        # 权限检查
        if not can_use_tool(role, tool_name):
            self._audit.log(
                role=role.value,
                action="tool_call",
                target=tool_name,
                detail=f"被拒绝：权限不足",
                allowed=False,
            )
            raise SecurityError(role, tool_name)

        # 执行工具
        result = self._registry.call(tool_name, **kwargs)

        # 记录审计日志
        self._audit.log(
            role=role.value,
            action="tool_call",
            target=tool_name,
            detail=f"参数: {kwargs}",
            allowed=True,
        )
        return result

    def get_audit_log(self) -> AuditLog:
        """获取审计日志实例。"""
        return self._audit
