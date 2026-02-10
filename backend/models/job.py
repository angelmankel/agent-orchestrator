"""Job queue models."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
from .base import generate_id

JobStatus = Literal["pending", "running", "done", "failed", "cancelled"]


class JobBase(BaseModel):
    """Base job fields."""

    job_type: str
    payload: dict
    priority: int = 0
    max_attempts: int = 3


class JobCreate(JobBase):
    """Fields for creating a job."""

    scheduled_at: Optional[datetime] = None


class JobUpdate(BaseModel):
    """Fields for updating a job."""

    status: Optional[JobStatus] = None
    error: Optional[str] = None
    result: Optional[dict] = None


class Job(JobBase):
    """Full job model."""

    id: str = Field(default_factory=generate_id)
    status: JobStatus = "pending"
    attempts: int = 0
    scheduled_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[dict] = None

    class Config:
        from_attributes = True
