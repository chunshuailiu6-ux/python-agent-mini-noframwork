"""MCP 多代理协作单元测试。"""

from __future__ import annotations

import threading
import time

from agent import Agent
from mcp import (
    AgentRegistry,
    AgentWorker,
    MCPClient,
    build_request,
    build_response,
    is_request,
    is_response,
    parse_message,
)


class TestProtocol:
    def test_build_request(self):
        req = build_request("run", {"input": "hi"}, request_id="123")
        msg = parse_message(req)
        assert msg["method"] == "run"
        assert msg["params"] == {"input": "hi"}
        assert msg["id"] == "123"

    def test_build_response(self):
        resp = build_response("123", result="ok")
        msg = parse_message(resp)
        assert msg["result"] == "ok"
        assert msg["id"] == "123"

    def test_build_error_response(self):
        resp = build_response("123", error={"code": -1, "message": "fail"})
        msg = parse_message(resp)
        assert msg["error"]["code"] == -1

    def test_is_request_and_response(self):
        req = parse_message(build_request("m"))
        resp = parse_message(build_response("1", result="x"))
        assert is_request(req) is True
        assert is_response(resp) is True

    def test_parse_invalid_json(self):
        import pytest
        with pytest.raises(ValueError):
            parse_message("not json")


class TestRegistry:
    def setup_method(self):
        self.reg = AgentRegistry()

    def test_register_and_get(self):
        self.reg.register("a1", "agent1", "tcp://127.0.0.1:5555", ["calc"])
        info = self.reg.get("a1")
        assert info is not None
        assert info.name == "agent1"

    def test_list_agents(self):
        self.reg.register("a1", "agent1", "tcp://1:5555")
        self.reg.register("a2", "agent2", "tcp://2:5555")
        assert len(self.reg.list_agents()) == 2

    def test_unregister(self):
        self.reg.register("a1", "agent1", "tcp://1:5555")
        assert self.reg.unregister("a1") is True
        assert self.reg.get("a1") is None

    def test_find_by_capability(self):
        self.reg.register("a1", "agent1", "tcp://1:5555", ["calculator"])
        self.reg.register("a2", "agent2", "tcp://2:5555", ["file_read"])
        found = self.reg.find_by_capability("calculator")
        assert len(found) == 1
        assert found[0].name == "agent1"

    def test_heartbeat(self):
        self.reg.register("a1", "agent1", "tcp://1:5555")
        assert self.reg.heartbeat("a1") is True
        assert self.reg.heartbeat("missing") is False


class TestTransport:
    def test_server_client_call(self):
        agent = Agent("worker")
        registry = AgentRegistry()
        worker = AgentWorker(agent, address="tcp://127.0.0.1:5577", registry=registry)
        worker.start()

        stop_event = threading.Event()

        def serve():
            while not stop_event.is_set():
                try:
                    worker.serve_once(timeout_ms=200)
                except Exception:
                    break

        t = threading.Thread(target=serve, daemon=True)
        t.start()
        time.sleep(0.3)

        client = MCPClient("tcp://127.0.0.1:5577")
        try:
            resp = client.call("list_tools")
            assert "calculator" in resp["result"]

            resp = client.call("run", {"input": "calc 2 + 2"})
            assert resp["result"] == "4"
        finally:
            stop_event.set()
            client.close()
            worker.stop()
            t.join(timeout=1)
