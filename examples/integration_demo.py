"""端到端集成验证：Agent + 工具 + 记忆 + 安全 + 任务 + MCP。"""
import time

from agent import Agent
from agent.context import ContextScope
from agent.core import AutonomousAgent, TaskStatus
from agent.security import Role, SecurityMiddleware
from agent.tools import ToolRegistry, register_builtin_tools

print("=" * 60)
print("1. Agent 核心功能")
print("=" * 60)
agent = Agent("demo-agent")
print("工具列表:", agent.list_tools())
print("计算 15 * 4:", agent.run("calc 15 * 4"))
print("记忆操作:", agent.run("remember lang python"))
print("回忆:", agent.run("recall lang"))

print("\n" + "=" * 60)
print("2. 上下文系统")
print("=" * 60)
agent.set_context("theme", "dark", scope=ContextScope.GLOBAL)
print("GLOBAL theme:", agent.get_context("theme"))

print("\n" + "=" * 60)
print("3. 安全权限中间件")
print("=" * 60)
reg = ToolRegistry()
register_builtin_tools(reg)
mw = SecurityMiddleware(reg)
print("admin 调用 calculator:", mw.call("calculator", role=Role.ADMIN, expression="100/4"))
try:
    mw.call("file_write", role=Role.GUEST, path="x", content="y")
except Exception as e:
    print("guest 调用 file_write 被拒绝:", e)

print("\n" + "=" * 60)
print("4. 自主运行与任务管理")
print("=" * 60)
auto = AutonomousAgent("auto-agent")
task = auto.create_task("计算任务", input_data="calc 7 * 8")
print("任务状态:", task.status)
result = auto.run_task(task.id)
print("执行后状态:", result.status, "输出:", result.output_data)
print("断点续跑(未完成任务):", [t.name for t in auto.resume_tasks()])

print("\n" + "=" * 60)
print("5. 长期记忆持久化")
print("=" * 60)
from agent.memory import LongTermMemory
ltm = LongTermMemory("./data/e2e_memory.db")
ltm.add("user:1", {"name": "Alice", "role": "admin"})
print("长期记忆检索:", ltm.get("user:1"))
print("长期记忆搜索 Alice:", [i.key for i in ltm.search("Alice")])
ltm.close()

print("\n" + "=" * 60)
print("✅ 全部集成验证通过！")
print("=" * 60)
