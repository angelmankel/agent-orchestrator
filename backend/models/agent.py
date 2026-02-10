"""Agent models."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
from .base import generate_id, TimestampMixin

AgentType = Literal["refinement", "development", "support", "planning"]
RunStatus = Literal["running", "success", "failed", "cancelled"]
LogLevel = Literal["debug", "info", "warn", "error"]


class AgentBase(BaseModel):
    """Base agent fields."""

    name: str
    description: str
    type: AgentType
    prompt: str
    tools: Optional[list[str]] = None
    model: str = "sonnet"
    config: Optional[dict] = None
    is_active: bool = True


class AgentCreate(AgentBase):
    """Fields for creating an agent."""

    project_id: Optional[str] = None


class AgentUpdate(BaseModel):
    """Fields for updating an agent."""

    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[AgentType] = None
    prompt: Optional[str] = None
    tools: Optional[list[str]] = None
    model: Optional[str] = None
    config: Optional[dict] = None
    is_active: Optional[bool] = None


class Agent(AgentBase, TimestampMixin):
    """Full agent model."""

    id: str = Field(default_factory=generate_id)
    project_id: Optional[str] = None

    class Config:
        from_attributes = True


class AgentRunCreate(BaseModel):
    """Fields for creating an agent run."""

    agent_id: str
    ticket_id: Optional[str] = None
    idea_id: Optional[str] = None
    input: Optional[dict] = None


class AgentRun(BaseModel):
    """Full agent run model."""

    id: str = Field(default_factory=generate_id)
    agent_id: str
    ticket_id: Optional[str] = None
    idea_id: Optional[str] = None
    status: RunStatus = "running"
    input: Optional[dict] = None
    output: Optional[dict] = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True


class RunLogCreate(BaseModel):
    """Fields for creating a run log entry."""

    run_id: str
    level: LogLevel
    message: str
    data: Optional[dict] = None


class RunLog(RunLogCreate):
    """Full run log model."""

    id: str = Field(default_factory=generate_id)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
