"""安全权限模块。

提供基于角色的访问控制（RBAC）、操作审计日志与权限中间件。

核心类：
    - Role: 角色枚举（admin / user / guest）。
    - AuditLog: 操作审计日志。
    - SecurityMiddleware: 权限检查中间件。
    - SecurityError: 权限不足异常。
"""

from .audit_log import AuditLog
from .middleware import SecurityError, SecurityMiddleware
from .rbac import Role, can_use_tool, role_has_permission

__all__ = [
    "Role",
    "AuditLog",
    "SecurityError",
    "SecurityMiddleware",
    "can_use_tool",
    "role_has_permission",
]
