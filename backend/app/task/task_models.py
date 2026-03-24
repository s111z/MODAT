"""
任务数据模型
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    QA = "qa"
    REVIEW = "review"


class Task(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    session_id: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    steps: List[str] = Field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
