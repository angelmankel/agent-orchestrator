"""Ticket models."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
from .base import generate_id, TimestampMixin

TicketType = Literal["feature", "bugfix", "refactor", "chore"]
TicketStatus = Literal["queued", "in_progress", "review", "blocked", "done", "cancelled"]
SubtaskStatus = Literal["pending", "in_progress", "done", "skipped"]


class TicketBase(BaseModel):
    """Base ticket fields."""

    title: str
    description: str
    type: TicketType
    priority: int = 0
    spec: Optional[dict] = None


class TicketCreate(TicketBase):
    """Fields for creating a ticket."""

    project_id: str
    idea_id: Optional[str] = None
    assigned_agent: Optional[str] = None


class TicketUpdate(BaseModel):
    """Fields for updating a ticket."""

    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[TicketType] = None
    status: Optional[TicketStatus] = None
    priority: Optional[int] = None
    assigned_agent: Optional[str] = None
    spec: Optional[dict] = None
    result: Optional[dict] = None


class Ticket(TicketBase, TimestampMixin):
    """Full ticket model."""

    id: str = Field(default_factory=generate_id)
    project_id: str
    idea_id: Optional[str] = None
    status: TicketStatus = "queued"
    assigned_agent: Optional[str] = None
    result: Optional[dict] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubtaskBase(BaseModel):
    """Base subtask fields."""

    title: str
    description: Optional[str] = None
    order_index: int = 0


class SubtaskCreate(SubtaskBase):
    """Fields for creating a subtask."""

    ticket_id: str
    agent_id: Optional[str] = None


class SubtaskUpdate(BaseModel):
    """Fields for updating a subtask."""

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[SubtaskStatus] = None
    order_index: Optional[int] = None
    agent_id: Optional[str] = None


class Subtask(SubtaskBase):
    """Full subtask model."""

    id: str = Field(default_factory=generate_id)
    ticket_id: str
    status: SubtaskStatus = "pending"
    agent_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
