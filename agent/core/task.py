"""任务状态管理与断点续跑。

提供任务状态机、JSON 持久化以及断点续跑能力。
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """任务状态。"""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


# 合法的状态转换
ALLOWED_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.PENDING: {TaskStatus.RUNNING, TaskStatus.FAILED},
    TaskStatus.RUNNING: {TaskStatus.PAUSED, TaskStatus.COMPLETED, TaskStatus.FAILED},
    TaskStatus.PAUSED: {TaskStatus.RUNNING, TaskStatus.FAILED},
    TaskStatus.COMPLETED: set(),
    TaskStatus.FAILED: {TaskStatus.PENDING},  # 失败后可重试
}


class Task(BaseModel):
    """任务数据模型。"""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    input_data: Any = None
    output_data: Any = None
    error: Optional[str] = None
    progress: int = 0  # 0-100
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def can_transition_to(self, new_status: TaskStatus) -> bool:
        return new_status in ALLOWED_TRANSITIONS.get(self.status, set())


class TaskManager:
    """任务管理器，支持状态持久化与断点续跑。

    Args:
        save_path: 任务状态持久化文件路径（JSON）。
    """

    def __init__(self, save_path: str = "./data/tasks.json") -> None:
        self.save_path = Path(save_path)
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        self._tasks: dict[str, Task] = {}
        self._load()

    # ------------------------------------------------------------------
    # 任务 CRUD
    # ------------------------------------------------------------------
    def create(self, name: str, description: str = "", input_data: Any = None) -> Task:
        """创建新任务。"""
        task = Task(name=name, description=description, input_data=input_data)
        self._tasks[task.id] = task
        self._save()
        return task

    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def list_tasks(self) -> list[Task]:
        return list(self._tasks.values())

    def list_by_status(self, status: TaskStatus) -> list[Task]:
        return [t for t in self._tasks.values() if t.status == status]

    # ------------------------------------------------------------------
    # 状态转换
    # ------------------------------------------------------------------
    def transition(self, task_id: str, new_status: TaskStatus, **kwargs: Any) -> Task:
        """转换任务状态。

        Args:
            task_id: 任务 ID。
            new_status: 目标状态。
            **kwargs: 额外更新字段（output_data, error, progress 等）。

        Returns:
            更新后的任务。

        Raises:
            ValueError: 状态转换不合法或任务不存在。
        """
        task = self._tasks.get(task_id)
        if task is None:
            raise ValueError(f"任务 {task_id} 不存在")
        if not task.can_transition_to(new_status):
            raise ValueError(f"不允许从 {task.status} 转换到 {new_status}")

        task.status = new_status
        task.updated_at = datetime.now()
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        self._save()
        return task

    def start(self, task_id: str) -> Task:
        return self.transition(task_id, TaskStatus.RUNNING)

    def pause(self, task_id: str) -> Task:
        return self.transition(task_id, TaskStatus.PAUSED)

    def complete(self, task_id: str, output_data: Any = None) -> Task:
        return self.transition(task_id, TaskStatus.COMPLETED, output_data=output_data)

    def fail(self, task_id: str, error: str) -> Task:
        return self.transition(task_id, TaskStatus.FAILED, error=error)

    def retry(self, task_id: str) -> Task:
        """失败任务重试：将状态重置为 pending。"""
        return self.transition(task_id, TaskStatus.PENDING)

    def update_progress(self, task_id: str, progress: int) -> Task:
        task = self._tasks.get(task_id)
        if task is None:
            raise ValueError(f"任务 {task_id} 不存在")
        task.progress = max(0, min(100, progress))
        task.updated_at = datetime.now()
        self._save()
        return task

    # ------------------------------------------------------------------
    # 持久化
    # ------------------------------------------------------------------
    def _save(self) -> None:
        data = {tid: task.model_dump(mode="json") for tid, task in self._tasks.items()}
        self.save_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load(self) -> None:
        if not self.save_path.exists():
            return
        try:
            data = json.loads(self.save_path.read_text(encoding="utf-8"))
            for tid, task_data in data.items():
                self._tasks[tid] = Task(**task_data)
        except Exception:
            # 文件损坏时忽略
            pass

    def resume(self) -> list[Task]:
        """断点续跑：返回所有未完成的任务（pending/running/paused）。"""
        unfinished = [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.PAUSED]
        return [t for t in self._tasks.values() if t.status in unfinished]

    def clear(self) -> None:
        """清空所有任务。"""
        self._tasks.clear()
        self._save()
