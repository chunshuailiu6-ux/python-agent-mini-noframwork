"""任务管理与断点续跑单元测试。"""

from __future__ import annotations

import pytest

from agent.core.task import TaskManager, TaskStatus


class TestTaskManager:
    def _make(self, tmp_path):
        return TaskManager(save_path=str(tmp_path / "tasks.json"))

    def test_create_task(self, tmp_path):
        tm = self._make(tmp_path)
        task = tm.create("demo", "测试任务")
        assert task.status == TaskStatus.PENDING
        assert task.name == "demo"

    def test_list_tasks(self, tmp_path):
        tm = self._make(tmp_path)
        tm.create("t1")
        tm.create("t2")
        assert len(tm.list_tasks()) == 2

    def test_status_transitions(self, tmp_path):
        tm = self._make(tmp_path)
        task = tm.create("t")
        tm.start(task.id)
        assert tm.get(task.id).status == TaskStatus.RUNNING
        tm.complete(task.id, output_data="done")
        assert tm.get(task.id).status == TaskStatus.COMPLETED

    def test_invalid_transition(self, tmp_path):
        tm = self._make(tmp_path)
        task = tm.create("t")
        with pytest.raises(ValueError):
            tm.complete(task.id)

    def test_pause_and_resume(self, tmp_path):
        tm = self._make(tmp_path)
        task = tm.create("t")
        tm.start(task.id)
        tm.pause(task.id)
        assert tm.get(task.id).status == TaskStatus.PAUSED
        tm.start(task.id)
        assert tm.get(task.id).status == TaskStatus.RUNNING

    def test_fail_and_retry(self, tmp_path):
        tm = self._make(tmp_path)
        task = tm.create("t")
        tm.start(task.id)
        tm.fail(task.id, error="boom")
        assert tm.get(task.id).status == TaskStatus.FAILED
        tm.retry(task.id)
        assert tm.get(task.id).status == TaskStatus.PENDING

    def test_progress(self, tmp_path):
        tm = self._make(tmp_path)
        task = tm.create("t")
        tm.update_progress(task.id, 50)
        assert tm.get(task.id).progress == 50

    def test_persistence(self, tmp_path):
        path = str(tmp_path / "persist.json")
        tm1 = TaskManager(save_path=path)
        task = tm1.create("persist_task")
        tm1.start(task.id)
        tm2 = TaskManager(save_path=path)
        loaded = tm2.get(task.id)
        assert loaded is not None
        assert loaded.name == "persist_task"
        assert loaded.status == TaskStatus.RUNNING

    def test_resume_unfinished(self, tmp_path):
        tm = self._make(tmp_path)
        t1 = tm.create("pending_task")
        t2 = tm.create("running_task")
        tm.start(t2.id)
        t3 = tm.create("done_task")
        tm.start(t3.id)
        tm.complete(t3.id)

        unfinished = tm.resume()
        ids = {t.id for t in unfinished}
        assert t1.id in ids
        assert t2.id in ids
        assert t3.id not in ids

    def test_list_by_status(self, tmp_path):
        tm = self._make(tmp_path)
        t1 = tm.create("a")
        t2 = tm.create("b")
        tm.start(t2.id)
        pending = tm.list_by_status(TaskStatus.PENDING)
        assert len(pending) == 1
        assert pending[0].id == t1.id
