# Python Mini-Agent 系统开发方案

> 本文件是 mini-agent 项目的**总开发方案与上下文参考文档**。后续每一次开发对话都应先阅读本文档，确保实现方向、技术选型与模块划分保持一致。

---

## 一、项目概述

开发一个轻量级 Python 智能代理（mini-agent）系统，实现 AI 代理的核心功能，包括：

- 上下文管理（Context）
- 记忆系统（Memory：短期 + 长期）
- 工具调用（Tools）
- 命令行界面（CLI）
- 多代理协作（MCP）
- 安全权限控制（Security）
- 自主运行与任务续跑（Autonomy & Resume）

**目标**：提供一个可扩展、易理解的 AI 代理开发框架，适合初学者学习和实践。

---

## 二、技术选型

> 下表为所有第三方依赖的**版本约束**，安装时请严格按此版本执行，避免因版本差异导致的兼容问题。

| 模块 | 库 | 版本约束 | 用途 | 选择理由 |
|------|-----|---------|------|---------|
| 核心语言 | Python | `>=3.9,<3.13` | 运行环境 | 语法简洁、生态丰富、适合 AI 开发 |
| 依赖管理 | Poetry | `>=1.6,<2.0` | 依赖与虚拟环境管理 | 简化依赖管理、虚拟环境隔离 |
| 数据模型 | pydantic | `>=2.5,<3.0` | 上下文数据模型定义与验证 | 类型安全、自动校验、序列化友好 |
| 记忆 | langchain | `>=0.1.0,<0.2.0` | 多种记忆策略 | 提供 ConversationBufferMemory 等开箱即用的记忆实现 |
| CLI | click | `>=8.1,<9.0` | 命令行界面构建 | 轻量级、语法简洁、文档完善 |
| 消息队列 | pyzmq | `>=25.0,<27.0` | 多代理间消息传递 | 轻量级、高性能、跨语言 |
| 任务调度 | apscheduler | `>=3.10,<4.0` | 定时任务与自主运行 | 轻量级、支持多种触发器 |
| 环境变量 | python-dotenv | `>=1.0,<2.0` | `.env` 配置加载 | 行业标准、零配置 |
| HTTP 请求 | httpx | `>=0.25,<0.28` | 网络请求工具（同步+异步） | 支持 HTTP/2、异步、连接池，比 requests 更现代 |
| HTTP 请求 | requests | `>=2.31,<3.0` | 网络请求工具（同步） | 生态最广、教程最多，与 httpx 并存供选择 |
| 文档 | mkdocs | `>=1.5,<2.0` | 静态文档站点生成 | 简单易用、支持 Markdown |
| 文档主题 | mkdocs-material | `>=9.4,<10.0` | MkDocs 主题 | 美观、搜索能力强 |
| 测试 | pytest | `>=7.4,<9.0` | 单元测试与集成测试 | 生态最广、插件丰富 |
| 测试 | pytest-asyncio | `>=0.21,<0.24` | 异步代码测试 | 与 pytest 无缝集成 |

### 依赖清单（requirements 片段）

可直接保存为 `requirements.txt` 使用（推荐优先用 Poetry 管理）：

```txt
pydantic>=2.5,<3.0
langchain>=0.1.0,<0.2.0
click>=8.1,<9.0
pyzmq>=25.0,<27.0
apscheduler>=3.10,<4.0
python-dotenv>=1.0,<2.0
httpx>=0.25,<0.28
requests>=2.31,<3.0
mkdocs>=1.5,<2.0
mkdocs-material>=9.4,<10.0
pytest>=7.4,<9.0
pytest-asyncio>=0.21,<0.24
```

---

## 三、系统架构设计

### 3.1 核心模块划分

```
mini-agent/
├── agent/                  # 代理核心模块
│   ├── core/               # 基础代理类与核心逻辑
│   ├── context/            # 上下文管理系统
│   ├── memory/             # 记忆系统实现
│   ├── tools/              # 工具注册与调用系统
│   └── security/           # 安全权限控制
├── cli/                    # 命令行界面实现
├── mcp/                    # 多代理协作模块
├── examples/               # 示例代码与使用案例
├── tests/                  # 测试用例
└── docs/                   # 项目文档
```

### 3.2 模块间关系

```
┌─────────────┐       ┌─────────────┐
│     CLI     │──────▶│  Agent Core │
└─────────────┘       └──────┬──────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Context  │  │  Memory  │  │  Tools   │
        └──────────┘  └──────────┘  └──────────┘
                             │
                      ┌──────▼──────┐
                      │     MCP     │  (多代理协作)
                      └─────────────┘
```

- **核心代理模块（agent）**：系统基础，所有能力的承载者。
- **CLI 模块**：用户交互入口，调用 Agent Core。
- **MCP 模块**：多代理通信与协作，依赖 Agent Core 提供的能力。
- **上下文与记忆**：被所有模块共享。

---

## 四、功能模块详细设计

### 4.1 上下文控制系统（Context）

- 实现上下文数据模型定义（使用 Pydantic `BaseModel`）。
- 提供上下文 **创建 / 更新 / 查询 / 删除** API。
- 上下文作用域管理：`global`（全局）、`session`（会话）、`temp`（临时）。
- 上下文序列化与反序列化（JSON / Pickle）。

**关键接口**：

```python
class ContextManager:
    def create(self, scope: str, key: str, value: Any) -> None: ...
    def get(self, scope: str, key: str, default: Any = None) -> Any: ...
    def update(self, scope: str, key: str, value: Any) -> None: ...
    def delete(self, scope: str, key: str) -> None: ...
    def serialize(self) -> str: ...
    def deserialize(self, data: str) -> None: ...
```

### 4.2 记忆系统（Memory）

- **短期记忆**：In-memory 存储（Python 字典），会话级别，进程退出即丢失。
- **长期记忆**：SQLite 存储（`sqlite3` 标准库），持久化到本地文件。
- 记忆检索与存储 API。
- 记忆优先级与过期策略（TTL）。

**关键接口**：

```python
class ShortTermMemory:
    def add(self, key: str, value: Any, ttl: int | None = None) -> None: ...
    def get(self, key: str) -> Any | None: ...
    def clear(self) -> None: ...

class LongTermMemory:
    def save(self, key: str, value: Any) -> None: ...
    def load(self, key: str) -> Any | None: ...
    def search(self, query: str) -> list[Any]: ...
```

### 4.3 工具系统（Tools）

- 工具基类定义（`BaseTool`）。
- 工具注册装饰器（`@register_tool`）。
- 工具调用接口（统一参数校验与异常处理）。
- 内置基础工具：
  - 文件操作（读、写、追加）
  - 网络请求（基于 `httpx` / `requests`）
  - 计算器

**关键接口**：

```python
class BaseTool:
    name: str
    description: str

    def run(self, **kwargs) -> Any: ...

@register_tool
class CalculatorTool(BaseTool):
    name = "calculator"
    description = "执行数学计算"
    def run(self, expression: str) -> str: ...

class ToolRegistry:
    def register(self, tool: BaseTool) -> None: ...
    def get(self, name: str) -> BaseTool | None: ...
    def list_tools(self) -> list[str]: ...
    def call(self, name: str, **kwargs) -> Any: ...
```

### 4.4 命令行界面（CLI）

基于 Click 实现：

- 代理启动命令：`mini-agent start`
- 代理状态查询：`mini-agent status`
- 任务提交与监控：`mini-agent task run` / `mini-agent task list`
- 系统配置管理：`mini-agent config show` / `mini-agent config set`

### 4.5 多代理协作（MCP）

- 代理注册与发现（基于 ZeroMQ 的 REQ/REP 模式）。
- 消息传递机制（JSON 序列化）。
- 任务分发与结果汇总。
- 代理间通信协议：JSON-RPC 2.0。

### 4.6 安全权限（Security）

- 用户角色定义：`admin` / `user` / `guest`。
- 权限检查中间件（在工具调用前校验角色权限）。
- 敏感操作访问控制（如文件写入、网络请求需 `user` 以上角色）。
- 操作日志记录（写入 SQLite 日志表）。

### 4.7 自主与续跑（Autonomy & Resume）

- 任务状态管理：`pending` / `running` / `paused` / `completed` / `failed`。
- 断点续跑机制：任务状态持久化（JSON 文件），重启后恢复。
- 异常处理与恢复：捕获异常 → 记录日志 → 重试或转入 `failed`。
- 自主决策逻辑框架：基于规则的简单决策树（预留 LLM 接入点）。

---

## 五、实施步骤

### 阶段一：环境搭建

1. 创建项目目录结构（见第三节）。
2. 初始化 Poetry 项目：`poetry init`。
3. 安装基础依赖包（按第二节版本约束）。
4. 配置开发环境（`.env`、`pyproject.toml`）。

### 阶段二：核心模块开发

1. 实现基础代理类（`agent/core/base_agent.py`）。
2. 开发上下文管理系统（`agent/context/`）。
3. 实现记忆系统（`agent/memory/`）。
4. 开发工具注册与调用机制（`agent/tools/`）。

### 阶段三：功能扩展

1. 开发 CLI 界面（`cli/`）。
2. 实现多代理协作功能（`mcp/`）。
3. 添加安全权限控制（`agent/security/`）。
4. 开发自主运行与续跑功能。

### 阶段四：文档编写

1. 使用 MkDocs 创建项目文档站点。
2. 编写 API 文档（`docs/api/`）。
3. 提供使用示例（`docs/examples/`）。
4. 整理开发指南（`docs/modules/`）。

### 阶段五：测试与优化

1. 编写单元测试（`tests/`）。
2. 进行集成测试。
3. 性能优化。
4. 用户体验改进。

---

## 六、项目文档结构（MD 文档）

```
docs/
├── index.md                 # 项目概述
├── installation.md          # 安装指南
├── quickstart.md            # 快速入门
├── architecture.md          # 系统架构
├── development-plan.md      # 本文件：总开发方案
├── modules/                 # 模块文档
│   ├── context.md           # 上下文系统
│   ├── memory.md            # 记忆系统
│   ├── tools.md             # 工具系统
│   ├── cli.md               # CLI 模块
│   ├── mcp.md               # 多代理协作
│   └── security.md          # 安全权限
├── examples/                # 使用示例
└── api/                     # API 文档
```

---

## 七、开发计划

| 阶段 | 周期 | 交付内容 |
|------|------|---------|
| 第一阶段 | 第 1-2 周 | 环境搭建、基础代理类、上下文系统、记忆系统 |
| 第二阶段 | 第 3-5 周 | 工具系统、CLI 界面、多代理协作 |
| 第三阶段 | 第 6-7 周 | 安全权限、自主运行、项目文档 |

---

## 八、注意事项

1. 本项目**暂不考虑 API Key 管理**，后续可扩展添加。
2. 作为学习项目，**优先考虑代码可读性和可理解性**，不过度追求性能。
3. 采用**增量开发**方式：先实现核心功能，再逐步扩展。
4. 定期提交代码，保持良好的版本控制习惯。
5. 每个功能模块开发完成后**编写相应的测试用例**。
6. 所有第三方依赖**严格按版本约束安装**（见第二节）。

---

## 九、小白学习路径建议

按以下顺序逐步实现，每完成一个模块就运行测试，确保理解后再进入下一个：

1. **Python 基础复习**：类与对象、装饰器、上下文管理器、类型注解。
2. **Pydantic**：学习 `BaseModel`、字段校验、序列化。
3. **上下文系统**：用 dict 实现最简单的键值存储 → 引入 Pydantic → 加作用域。
4. **记忆系统**：短期记忆（dict）→ 长期记忆（sqlite3）→ 加 TTL。
5. **工具系统**：装饰器注册 → BaseTool 基类 → 内置工具。
6. **基础代理类**：把 Context + Memory + Tools 组合起来。
7. **CLI**：用 Click 包装代理类，提供命令行入口。
8. **安全权限**：在工具调用前加权限校验。
9. **MCP**：用 ZeroMQ 实现两个代理的通信。
10. **自主与续跑**：任务状态机 + JSON 持久化。

---

*文档版本：v1.0 | 创建日期：2026-10-01*
