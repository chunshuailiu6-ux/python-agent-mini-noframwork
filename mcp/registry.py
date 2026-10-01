"""代理注册与发现中心。

管理所有代理的注册信息，提供查询与心跳机制。
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AgentInfo(BaseModel):
    """代理注册信息。"""

    agent_id: str
    name: str
    address: str  # ZeroMQ 地址
    capabilities: list[str] = Field(default_factory=list)
    registered_at: datetime = Field(default_factory=datetime.now)
    last_heartbeat: float = Field(default_factory=time.time)


class AgentRegistry:
    """代理注册中心（内存实现）。

    提供代理注册、注销、查询与心跳保活。
    """

    def __init__(self, heartbeat_timeout: float = 30.0) -> None:
        self._agents: dict[str, AgentInfo] = {}
        self._heartbeat_timeout = heartbeat_timeout

    def register(self, agent_id: str, name: str, address: str, capabilities: Optional[list[str]] = None) -> AgentInfo:
        """注册代理。"""
        info = AgentInfo(
            agent_id=agent_id,
            name=name,
            address=address,
            capabilities=capabilities or [],
        )
        self._agents[agent_id] = info
        return info

    def unregister(self, agent_id: str) -> bool:
        """注销代理。"""
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    def heartbeat(self, agent_id: str) -> bool:
        """代理心跳。"""
        if agent_id in self._agents:
            self._agents[agent_id].last_heartbeat = time.time()
            return True
        return False

    def get(self, agent_id: str) -> Optional[AgentInfo]:
        """查询代理。"""
        return self._agents.get(agent_id)

    def list_agents(self) -> list[AgentInfo]:
        """列出所有在线代理（自动剔除超时的）。"""
        self._cleanup()
        return list(self._agents.values())

    def find_by_capability(self, capability: str) -> list[AgentInfo]:
        """按能力查找代理。"""
        self._cleanup()
        return [a for a in self._agents.values() if capability in a.capabilities]

    def _cleanup(self) -> None:
        """剔除心跳超时的代理。"""
        now = time.time()
        expired = [
            aid for aid, info in self._agents.items()
            if now - info.last_heartbeat > self._heartbeat_timeout
        ]
        for aid in expired:
            del self._agents[aid]
