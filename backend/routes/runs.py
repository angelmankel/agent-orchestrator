"""Agent run endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Optional

from database import get_db
from models import Agent, AgentRunCreate, AgentRun
from agents import AgentRuntime
from routes.agents import _row_to_agent

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=AgentRun, status_code=201)
async def create_run(run_request: AgentRunCreate):
    """Execute an agent and return the run result."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM agents WHERE id = ?", (run_request.agent_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Agent not found")

        agent = _row_to_agent(row)
    finally:
        await db.close()

    try:
        runtime = AgentRuntime()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    input_data = run_request.input or {}
    result = await runtime.run_agent(
        agent=agent,
        input_data=input_data,
        ticket_id=run_request.ticket_id,
        idea_id=run_request.idea_id,
    )

    return result


@router.get("/{run_id}", response_model=AgentRun)
async def get_run(run_id: str):
    """Get a run by ID."""
    import json

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM agent_runs WHERE id = ?", (run_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Run not found")

        input_data = json.loads(row["input"]) if row["input"] else None
        output_data = json.loads(row["output"]) if row["output"] else None

        return AgentRun(
            id=row["id"],
            agent_id=row["agent_id"],
            ticket_id=row["ticket_id"],
            idea_id=row["idea_id"],
            status=row["status"],
            input=input_data,
            output=output_data,
            tokens_used=row["tokens_used"],
            cost_usd=row["cost_usd"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            error=row["error"],
        )
    finally:
        await db.close()
