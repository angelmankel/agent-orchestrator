"""API routes."""

from .health import router as health_router
from .projects import router as projects_router
from .ideas import router as ideas_router
from .agents import router as agents_router
from .tickets import router as tickets_router
from .runs import router as runs_router
from .questions import router as questions_router

__all__ = [
    "health_router",
    "projects_router",
    "ideas_router",
    "agents_router",
    "tickets_router",
    "runs_router",
    "questions_router",
]
