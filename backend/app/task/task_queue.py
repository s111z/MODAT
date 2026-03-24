"""
任务队列

支持异步任务提交、状态查询和结果获取。
用于处理长时间运行的审核任务。
"""

import asyncio
from typing import Optional, Dict
from datetime import datetime

from .task_models import Task, TaskStatus, TaskType


class TaskQueue:
    """异步任务队列"""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.queue: asyncio.Queue = asyncio.Queue()
        self._running = False

    async def submit(self, task: Task) -> str:
        """提交任务到队列"""
        self.tasks[task.task_id] = task
        await self.queue.put(task.task_id)
        return task.task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务信息"""
        return self.tasks.get(task_id)

    def update_status(self, task_id: str, status: TaskStatus, **kwargs):
        """更新任务状态"""
        task = self.tasks.get(task_id)
        if task:
            task.status = status
            task.updated_at = datetime.now()
            if "result" in kwargs:
                task.result = kwargs["result"]
            if "error" in kwargs:
                task.error = kwargs["error"]
            if "steps" in kwargs:
                task.steps = kwargs["steps"]

    def add_step(self, task_id: str, step: str):
        """为任务添加步骤"""
        task = self.tasks.get(task_id)
        if task:
            task.steps.append(step)
            task.updated_at = datetime.now()

    def list_tasks(self, session_id: str = None, limit: int = 20) -> list[Task]:
        """列出任务"""
        tasks = list(self.tasks.values())
        if session_id:
            tasks = [t for t in tasks if t.session_id == session_id]
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks[:limit]

    async def start_worker(self, handler):
        """启动任务处理worker"""
        self._running = True
        while self._running:
            try:
                task_id = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                task = self.tasks.get(task_id)
                if task and task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.RUNNING
                    task.updated_at = datetime.now()
                    try:
                        result = await handler(task)
                        task.status = TaskStatus.COMPLETED
                        task.result = result
                    except Exception as e:
                        task.status = TaskStatus.FAILED
                        task.error = str(e)
                    task.updated_at = datetime.now()
            except asyncio.TimeoutError:
                continue
            except Exception:
                continue

    def stop_worker(self):
        """停止worker"""
        self._running = False


# 全局任务队列
task_queue = TaskQueue()
