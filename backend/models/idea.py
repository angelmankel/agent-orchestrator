"""Idea models."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
from .base import generate_id, TimestampMixin

IdeaStatus = Literal["pending", "refining", "questions", "approved", "rejected", "converted"]
IdeaSource = Literal["web", "api", "cli"]


class IdeaBase(BaseModel):
    """Base idea fields."""

    title: str
    description: str
    source: Optional[IdeaSource] = None
    priority: int = 0
    metadata: Optional[dict] = None


class IdeaCreate(IdeaBase):
    """Fields for creating an idea."""

    project_id: str


class IdeaUpdate(BaseModel):
    """Fields for updating an idea."""

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IdeaStatus] = None
    priority: Optional[int] = None
    metadata: Optional[dict] = None


class Idea(IdeaBase, TimestampMixin):
    """Full idea model."""

    id: str = Field(default_factory=generate_id)
    project_id: str
    status: IdeaStatus = "pending"

    class Config:
        from_attributes = True


class QuestionBase(BaseModel):
    """Base question fields."""

    question: str
    context: Optional[str] = None


class QuestionCreate(QuestionBase):
    """Fields for creating a question."""

    idea_id: str
    agent_id: str


class QuestionAnswer(BaseModel):
    """Fields for answering a question."""

    answer: str


class Question(QuestionBase):
    """Full question model."""

    id: str = Field(default_factory=generate_id)
    idea_id: str
    agent_id: str
    answer: Optional[str] = None
    status: Literal["pending", "answered", "skipped"] = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    answered_at: Optional[datetime] = None

    class Config:
        from_attributes = True
