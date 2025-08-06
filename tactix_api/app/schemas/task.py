from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.task import TaskPriority, TaskStatus
from app.schemas.user import User


# Shared properties
class TaskBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None


# Properties to receive via API on creation
class TaskCreate(TaskBase):
    title: str
    project_id: int


# Properties to receive via API on update
class TaskUpdate(TaskBase):
    pass


# Properties shared by models stored in DB
class TaskInDBBase(TaskBase):
    id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Additional properties to return via API
class Task(TaskInDBBase):
    pass


# Additional properties to return via API with related data
class TaskWithDetails(Task):
    assignee: Optional[User] = None
    created_by: User