"""安全权限单元测试。"""

from __future__ import annotations

import pytest

from agent.security import (
    AuditLog,
    Role,
    SecurityError,
    SecurityMiddleware,
    can_use_tool,
)
from agent.tools import ToolRegistry, register_builtin_tools


class TestRBAC:
    def test_guest_can_calculator(self):
        assert can_use_tool(Role.GUEST, "calculator") is True

    def test_guest_cannot_file_write(self):
        assert can_use_tool(Role.GUEST, "file_write") is False

    def test_user_can_file_write(self):
        assert can_use_tool(Role.USER, "file_write") is True

    def test_admin_can_all(self):
        assert can_use_tool(Role.ADMIN, "calculator") is True
        assert can_use_tool(Role.ADMIN, "file_write") is True
        assert can_use_tool(Role.ADMIN, "web_request") is True


class TestSecurityMiddleware:
    def _make(self, tmp_path):
        reg = ToolRegistry()
        register_builtin_tools(reg)
        audit = AuditLog(str(tmp_path / "audit.db"))
        return SecurityMiddleware(reg, audit_log=audit)

    def test_allowed_call(self, tmp_path):
        mw = self._make(tmp_path)
        result = mw.call("calculator", role=Role.ADMIN, expression="1+1")
        assert result == "2"

    def test_denied_call(self, tmp_path):
        mw = self._make(tmp_path)
        with pytest.raises(SecurityError):
            mw.call("file_write", role=Role.GUEST, path="x", content="y")

    def test_audit_log_recorded(self, tmp_path):
        mw = self._make(tmp_path)
        mw.call("calculator", role=Role.USER, expression="1+1")
        logs = mw.get_audit_log().query()
        assert len(logs) >= 1
        assert logs[0]["target"] == "calculator"
        assert logs[0]["allowed"] == 1

    def test_audit_log_denied(self, tmp_path):
        mw = self._make(tmp_path)
        try:
            mw.call("file_write", role=Role.GUEST, path="x", content="y")
        except SecurityError:
            pass
        logs = mw.get_audit_log().query()
        denied = [l for l in logs if l["allowed"] == 0]
        assert len(denied) == 1
        assert denied[0]["target"] == "file_write"

    def test_default_role(self, tmp_path):
        reg = ToolRegistry()
        register_builtin_tools(reg)
        mw = SecurityMiddleware(reg, default_role=Role.GUEST)
        result = mw.call("calculator", expression="1+1")
        assert result == "2"
