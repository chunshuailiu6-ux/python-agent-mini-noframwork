"""上下文管理系统。

提供上下文数据的存储、检索、作用域管理与序列化能力。

核心类：
    - ContextManager: 上下文管理器，提供完整的 CRUD API。
    - ContextScope: 作用域枚举（GLOBAL / SESSION / TEMP）。
    - ContextItem: 单个上下文条目（含元数据）。
"""

from .manager import ContextManager
from .models import ContextItem, ContextScope, ContextSnapshot

__all__ = ["ContextManager", "ContextItem", "ContextScope", "ContextSnapshot"]
