"""命令行界面（CLI）。

基于 Click 实现，提供代理启动、状态查询、任务管理与配置管理命令。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click

from agent import Agent
from agent.tools import ToolRegistry, register_builtin_tools

# 配置文件路径
CONFIG_PATH = Path("./data/cli_config.json")


def _load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {"agent_name": "mini-agent", "role": "user"}


def _save_config(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


def _create_agent(config: dict) -> Agent:
    registry = ToolRegistry()
    register_builtin_tools(registry)
    return Agent(name=config.get("agent_name", "mini-agent"), tools=registry)


@click.group()
@click.version_option("0.1.0", prog_name="mini-agent")
def cli() -> None:
    """Mini-Agent 命令行工具。"""


# ------------------------------------------------------------------
# start: 启动交互式对话
# ------------------------------------------------------------------
@cli.command()
@click.option("--name", default=None, help="代理名称")
def start(name: Optional[str]) -> None:
    """启动交互式代理对话。"""
    config = _load_config()
    if name:
        config["agent_name"] = name
    agent = _create_agent(config)
    click.echo(f"🤖 {agent.name} 已启动。输入 'exit' 退出，'tools' 查看工具。")
    while True:
        try:
            user_input = click.prompt("你", type=str)
        except (click.Abort, EOFError):
            break
        if user_input.strip().lower() in ("exit", "quit", "q"):
            click.echo("再见！")
            break
        response = agent.run(user_input)
        click.echo(f"{agent.name}: {response}")


# ------------------------------------------------------------------
# status: 状态查询
# ------------------------------------------------------------------
@cli.command()
def status() -> None:
    """查询代理状态。"""
    config = _load_config()
    agent = _create_agent(config)
    click.echo(f"代理名称: {agent.name}")
    click.echo(f"可用工具: {', '.join(agent.list_tools())}")
    click.echo(f"上下文键数: {len(agent.context)}")
    click.echo(f"记忆条数: {len(agent.memory)}")


# ------------------------------------------------------------------
# task: 任务管理
# ------------------------------------------------------------------
@cli.group()
def task() -> None:
    """任务管理。"""


@task.command("run")
@click.argument("command_text")
def task_run(command_text: str) -> None:
    """运行单条任务命令。"""
    config = _load_config()
    agent = _create_agent(config)
    result = agent.run(command_text)
    click.echo(result)


@task.command("list")
def task_list() -> None:
    """列出历史任务（从记忆中读取）。"""
    config = _load_config()
    agent = _create_agent(config)
    keys = agent.memory.keys()
    if not keys:
        click.echo("暂无历史任务。")
        return
    click.echo("历史任务:")
    for key in keys:
        click.echo(f"  - {key}: {agent.memory.get(key)}")


# ------------------------------------------------------------------
# config: 配置管理
# ------------------------------------------------------------------
@cli.group()
def config() -> None:
    """系统配置管理。"""


@config.command("show")
def config_show() -> None:
    """显示当前配置。"""
    config = _load_config()
    click.echo(json.dumps(config, ensure_ascii=False, indent=2))


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """设置配置项。"""
    config = _load_config()
    config[key] = value
    _save_config(config)
    click.echo(f"已设置 {key} = {value}")


def main() -> None:
    """CLI 入口函数。"""
    cli()


if __name__ == "__main__":
    main()
