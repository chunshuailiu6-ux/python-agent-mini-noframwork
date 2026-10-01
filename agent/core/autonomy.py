"""自主运行模块。

在基础 Agent 之上增加定时任务调度与自主决策能力。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Optional

from apscheduler.schedulers.background import BackgroundScheduler

from .base_agent import Agent
from .task import Task, TaskManager, TaskStatus


class AutonomousAgent(Agent):
    """自主运行代理。

    在基础 Agent 之上增加：
    - 定时任务调度（基于 APScheduler）。
    - 任务状态管理与断点续跑。
    - 简单的自主决策框架（预留 LLM 接入点）。
    """

    def __init__(self, name: str = "mini-agent", task_save_path: str = "./data/tasks.json", **kwargs: Any) -> None:
        super().__init__(name=name, **kwargs)
        self.task_manager = TaskManager(save_path=task_save_path)
        self._scheduler: Optional[BackgroundScheduler] = None
        self._decision_handler: Optional[Callable[[str], str]] = None

    # ------------------------------------------------------------------
    # 任务调度
    # ------------------------------------------------------------------
    def start_scheduler(self) -> None:
        """启动后台调度器。"""
        if self._scheduler is not None:
            return
        self._scheduler = BackgroundScheduler()
        self._scheduler.start()

    def stop_scheduler(self) -> None:
        """停止调度器。"""
        if self._scheduler is not None:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None

    def schedule_task(
        self,
        func: Callable,
        trigger: str = "interval",
        seconds: int = 60,
        job_id: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """调度一个定时任务。

        Args:
            func: 要执行的函数。
            trigger: 触发器类型（interval/date/cron）。
            seconds: interval 触发器的间隔秒数。
            job_id: 任务 ID，默认自动生成。
            **kwargs: 其他 APScheduler 参数。

        Returns:
            任务 ID。
        """
        if self._scheduler is None:
            self.start_scheduler()
        job = self._scheduler.add_job(func, trigger, seconds=seconds, id=job_id, **kwargs)
        return job.id

    def remove_scheduled_task(self, job_id: str) -> None:
        """移除定时任务。"""
        if self._scheduler is not None:
            self._scheduler.remove_job(job_id)

    # ------------------------------------------------------------------
    # 任务管理（委托给 TaskManager）
    # ------------------------------------------------------------------
    def create_task(self, name: str, description: str = "", input_data: Any = None) -> Task:
        return self.task_manager.create(name, description, input_data)

    def run_task(self, task_id: str, executor: Optional[Callable[[Task], Any]] = None) -> Task:
        """执行一个任务，支持异常处理与状态更新。

        Args:
            task_id: 任务 ID。
            executor: 任务执行函数，接收 Task 返回结果。为 None 时使用默认执行器。

        Returns:
            执行后的任务。
        """
        task = self.task_manager.get(task_id)
        if task is None:
            raise ValueError(f"任务 {task_id} 不存在")

        # 如果是失败状态，先重置为 pending
        if task.status == TaskStatus.FAILED:
            self.task_manager.retry(task_id)

        self.task_manager.start(task_id)
        try:
            if executor is not None:
                result = executor(task)
            else:
                result = self._default_executor(task)
            self.task_manager.complete(task_id, output_data=result)
        except Exception as e:
            self.task_manager.fail(task_id, error=str(e))
        return self.task_manager.get(task_id)

    def _default_executor(self, task: Task) -> Any:
        """默认任务执行器：将 input_data 作为用户输入交给 run 处理。"""
        if task.input_data is None:
            return "无输入数据"
        return self.run(str(task.input_data))

    def resume_tasks(self) -> list[Task]:
        """断点续跑：恢复所有未完成任务并重新执行。"""
        unfinished = self.task_manager.resume()
        for task in unfinished:
            # 仅重试 pending/running 状态的任务
            if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
                self.run_task(task.id)
        return unfinished

    # ------------------------------------------------------------------
    # 自主决策（预留 LLM 接入点）
    # ------------------------------------------------------------------
    def set_decision_handler(self, handler: Callable[[str], str]) -> None:
        """设置自主决策处理器。

        可接入 LLM 实现智能决策。handler 接收用户输入，返回决策结果。
        """
        self._decision_handler = handler

    def decide(self, user_input: str) -> str:
        """自主决策：如果设置了决策处理器则调用，否则使用规则判断。"""
        if self._decision_handler is not None:
            return self._decision_handler(user_input)
        # 简单规则：包含关键词则认为需要工具调用
        keywords = ["计算", "读取", "写入", "文件", "网络", "请求"]
        if any(kw in user_input for kw in keywords):
            return "need_tool"
        return "direct_response"
