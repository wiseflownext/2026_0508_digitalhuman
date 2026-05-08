from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TaskCreateResponse(BaseModel):
    task_id: str
    status: str = "queued"


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    video_url: Optional[str] = None
    created_at: Optional[str] = None


class TaskItem(BaseModel):
    id: int
    task_id: str
    prompt: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    status: str
    created_at: str
    updated_at: str


class TaskListResponse(BaseModel):
    tasks: list[TaskItem]


class HealthResponse(BaseModel):
    status: str = "ok"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
