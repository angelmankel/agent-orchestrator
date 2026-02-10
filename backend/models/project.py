"""Project models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from .base import generate_id, TimestampMixin


class ProjectBase(BaseModel):
    """Base project fields."""

    name: str
    description: Optional[str] = None
    path: str
    config: Optional[dict] = None


class ProjectCreate(ProjectBase):
    """Fields for creating a project."""

    pass


class ProjectUpdate(BaseModel):
    """Fields for updating a project."""

    name: Optional[str] = None
    description: Optional[str] = None
    path: Optional[str] = None
    config: Optional[dict] = None


class Project(ProjectBase, TimestampMixin):
    """Full project model."""

    id: str = Field(default_factory=generate_id)

    class Config:
        from_attributes = True
