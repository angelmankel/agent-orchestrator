"""Agent CRUD endpoints."""

import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
import aiosqlite

from database import get_db
from models import Agent, AgentCreate, AgentUpdate, AgentRun, AgentRunCreate
from models.base import generate_id

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[Agent])
async def list_agents(
    project_id: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    active_only: bool = Query(True),
):
    """List agents with optional filtering."""
    db = await get_db()
    try:
        query = "SELECT * FROM agents WHERE 1=1"
        params = []

        if project_id:
            query += " AND (project_id = ? OR project_id IS NULL)"
            params.append(project_id)
        if type:
            query += " AND type = ?"
            params.append(type)
        if active_only:
            query += " AND is_active = 1"

        query += " ORDER BY name ASC"

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [_row_to_agent(row) for row in rows]
    finally:
        await db.close()


@router.post("", response_model=Agent, status_code=201)
async def create_agent(agent: AgentCreate):
    """Create a new agent."""
    db = await get_db()
    try:
        if agent.project_id:
            cursor = await db.execute(
                "SELECT id FROM projects WHERE id = ?", (agent.project_id,)
            )
            if not await cursor.fetchone():
                raise HTTPException(status_code=404, detail="Project not found")

        agent_id = generate_id()
        tools_json = json.dumps(agent.tools) if agent.tools else None
        config_json = json.dumps(agent.config) if agent.config else None

        await db.execute(
            """
            INSERT INTO agents (id, project_id, name, description, type, prompt, tools, model, config, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                agent_id,
                agent.project_id,
                agent.name,
                agent.description,
                agent.type,
                agent.prompt,
                tools_json,
                agent.model,
                config_json,
                1 if agent.is_active else 0,
            ),
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        row = await cursor.fetchone()
        return _row_to_agent(row)
    finally:
        await db.close()


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str):
    """Get an agent by ID."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Agent not found")
        return _row_to_agent(row)
    finally:
        await db.close()


@router.patch("/{agent_id}", response_model=Agent)
async def update_agent(agent_id: str, updates: AgentUpdate):
    """Update an agent."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Agent not found")

        update_data = updates.model_dump(exclude_unset=True)
        if not update_data:
            return _row_to_agent(row)

        if "tools" in update_data:
            update_data["tools"] = json.dumps(update_data["tools"])
        if "config" in update_data:
            update_data["config"] = json.dumps(update_data["config"])
        if "is_active" in update_data:
            update_data["is_active"] = 1 if update_data["is_active"] else 0

        update_data["updated_at"] = datetime.utcnow().isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in update_data.keys())
        values = list(update_data.values()) + [agent_id]

        await db.execute(
            f"UPDATE agents SET {set_clause} WHERE id = ?",
            values,
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        row = await cursor.fetchone()
        return _row_to_agent(row)
    finally:
        await db.close()


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: str):
    """Delete an agent."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Agent not found")

        await db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        await db.commit()
    finally:
        await db.close()


@router.get("/{agent_id}/runs", response_model=list[AgentRun])
async def list_agent_runs(agent_id: str, limit: int = Query(50, le=100)):
    """List runs for an agent."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Agent not found")

        cursor = await db.execute(
            """
            SELECT * FROM agent_runs
            WHERE agent_id = ?
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (agent_id, limit),
        )
        rows = await cursor.fetchall()
        return [_row_to_run(row) for row in rows]
    finally:
        await db.close()


def _row_to_agent(row: aiosqlite.Row) -> Agent:
    """Convert database row to Agent model."""
    tools = json.loads(row["tools"]) if row["tools"] else None
    config = json.loads(row["config"]) if row["config"] else None
    return Agent(
        id=row["id"],
        project_id=row["project_id"],
        name=row["name"],
        description=row["description"],
        type=row["type"],
        prompt=row["prompt"],
        tools=tools,
        model=row["model"],
        config=config,
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_run(row: aiosqlite.Row) -> AgentRun:
    """Convert database row to AgentRun model."""
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
