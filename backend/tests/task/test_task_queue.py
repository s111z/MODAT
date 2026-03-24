"""TaskModels + TaskQueue 单元测试"""

import pytest
import asyncio
from task.task_models import Task, TaskStatus, TaskType
from task.task_queue import TaskQueue


@pytest.mark.unit
class TestTaskModels:

    def test_task_defaults(self):
        task = Task(task_type=TaskType.QA)
        assert task.task_id  # 自动生成
        assert task.status == TaskStatus.PENDING
        assert task.steps == []
        assert task.result is None

    def test_task_status_enum(self):
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.CANCELLED == "cancelled"

    def test_task_type_enum(self):
        assert TaskType.QA == "qa"
        assert TaskType.REVIEW == "review"

    def test_task_with_data(self):
        task = Task(
            task_type=TaskType.REVIEW,
            session_id="s1",
            input_data={"message": "审核请求"},
        )
        assert task.session_id == "s1"
        assert task.input_data["message"] == "审核请求"


@pytest.mark.unit
class TestTaskQueue:

    def setup_method(self):
        self.queue = TaskQueue()

    def test_submit(self):
        task = Task(task_type=TaskType.QA, session_id="s1")
        loop = asyncio.get_event_loop()
        task_id = loop.run_until_complete(self.queue.submit(task))
        assert task_id == task.task_id
        assert task_id in self.queue.tasks

    def test_get_task(self):
        task = Task(task_type=TaskType.QA)
        asyncio.get_event_loop().run_until_complete(self.queue.submit(task))
        found = self.queue.get_task(task.task_id)
        assert found is task

    def test_get_task_not_found(self):
        assert self.queue.get_task("nonexistent") is None

    def test_update_status(self):
        task = Task(task_type=TaskType.QA)
        asyncio.get_event_loop().run_until_complete(self.queue.submit(task))
        self.queue.update_status(task.task_id, TaskStatus.RUNNING)
        assert task.status == TaskStatus.RUNNING

    def test_update_status_with_result(self):
        task = Task(task_type=TaskType.QA)
        asyncio.get_event_loop().run_until_complete(self.queue.submit(task))
        self.queue.update_status(
            task.task_id, TaskStatus.COMPLETED,
            result={"answer": "完成"}
        )
        assert task.status == TaskStatus.COMPLETED
        assert task.result["answer"] == "完成"

    def test_add_step(self):
        task = Task(task_type=TaskType.QA)
        asyncio.get_event_loop().run_until_complete(self.queue.submit(task))
        self.queue.add_step(task.task_id, "步骤1")
        self.queue.add_step(task.task_id, "步骤2")
        assert len(task.steps) == 2

    def test_list_tasks(self):
        loop = asyncio.get_event_loop()
        t1 = Task(task_type=TaskType.QA, session_id="s1")
        t2 = Task(task_type=TaskType.REVIEW, session_id="s2")
        t3 = Task(task_type=TaskType.QA, session_id="s1")
        loop.run_until_complete(self.queue.submit(t1))
        loop.run_until_complete(self.queue.submit(t2))
        loop.run_until_complete(self.queue.submit(t3))

        all_tasks = self.queue.list_tasks()
        assert len(all_tasks) == 3

        s1_tasks = self.queue.list_tasks(session_id="s1")
        assert len(s1_tasks) == 2

    def test_list_tasks_limit(self):
        loop = asyncio.get_event_loop()
        for i in range(5):
            loop.run_until_complete(
                self.queue.submit(Task(task_type=TaskType.QA))
            )
        limited = self.queue.list_tasks(limit=3)
        assert len(limited) == 3
