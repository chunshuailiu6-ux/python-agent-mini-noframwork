"""基于角色的访问控制（RBAC）。

定义角色、权限以及角色到权限的映射关系。
"""

from __future__ import annotations

from enum import Enum
from typing import Optional


class Role(str, Enum):
    """用户角色。"""

    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


# 工具到所需权限的映射。
# 权限名约定：tool:<工具名>
TOOL_PERMISSIONS: dict[str, str] = {
    "calculator": "tool:calculator",
    "file_read": "tool:file_read",
    "file_write": "tool:file_write",
    "web_request": "tool:web_request",
}

# 角色到权限的映射。
# admin 拥有所有权限，user 拥有除敏感操作外的权限，guest 仅可使用计算器。
ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: set(TOOL_PERMISSIONS.values()),
    Role.USER: {
        "tool:calculator",
        "tool:file_read",
        "tool:file_write",
        "tool:web_request",
    },
    Role.GUEST: {
        "tool:calculator",
    },
}


def get_permission_for_tool(tool_name: str) -> Optional[str]:
    """获取工具所需的权限。"""
    return TOOL_PERMISSIONS.get(tool_name)


def role_has_permission(role: Role, permission: str) -> bool:
    """判断角色是否拥有指定权限。"""
    return permission in ROLE_PERMISSIONS.get(role, set())


def can_use_tool(role: Role, tool_name: str) -> bool:
    """判断角色是否可以使用指定工具。"""
    permission = get_permission_for_tool(tool_name)
    if permission is None:
        # 未在权限表中登记的工具，默认 admin 可用
        return role == Role.ADMIN
    return role_has_permission(role, permission)
