"""Health check endpoints."""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Agent Orchestrator API",
        "version": "0.1.0",
        "docs": "/docs",
    }
