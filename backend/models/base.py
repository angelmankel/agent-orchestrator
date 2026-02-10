"""Base models and utilities."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid7 import uuid7


def generate_id() -> str:
    """Generate a time-sortable UUID7."""
    return str(uuid7())


class TimestampMixin(BaseModel):
    """Mixin for created_at and updated_at fields."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class APIResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool = True
    data: Optional[dict] = None
    error: Optional[str] = None
