"""Idea CRUD and pipeline endpoints."""

import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
import aiosqlite

from database import get_db
from models import Idea, IdeaCreate, IdeaUpdate, Ticket, Question
from models.base import generate_id

router = APIRouter(prefix="/ideas", tags=["ideas"])


@router.get("", response_model=list[Idea])
async def list_ideas(
    project_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """List ideas with optional filtering."""
    db = await get_db()
    try:
        query = "SELECT * FROM ideas WHERE 1=1"
        params = []

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY priority DESC, created_at DESC"

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [_row_to_idea(row) for row in rows]
    finally:
        await db.close()


@router.post("", response_model=Idea, status_code=201)
async def create_idea(idea: IdeaCreate):
    """Create a new idea."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id FROM projects WHERE id = ?", (idea.project_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")

        idea_id = generate_id()
        metadata_json = json.dumps(idea.metadata) if idea.metadata else None

        await db.execute(
            """
            INSERT INTO ideas (id, project_id, title, description, source, priority, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                idea_id,
                idea.project_id,
                idea.title,
                idea.description,
                idea.source,
                idea.priority,
                metadata_json,
            ),
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,))
        row = await cursor.fetchone()
        return _row_to_idea(row)
    finally:
        await db.close()


@router.get("/{idea_id}", response_model=Idea)
async def get_idea(idea_id: str):
    """Get an idea by ID."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Idea not found")
        return _row_to_idea(row)
    finally:
        await db.close()


@router.patch("/{idea_id}", response_model=Idea)
async def update_idea(idea_id: str, updates: IdeaUpdate):
    """Update an idea."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Idea not found")

        update_data = updates.model_dump(exclude_unset=True)
        if not update_data:
            return _row_to_idea(row)

        if "metadata" in update_data:
            update_data["metadata"] = json.dumps(update_data["metadata"])

        update_data["updated_at"] = datetime.utcnow().isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in update_data.keys())
        values = list(update_data.values()) + [idea_id]

        await db.execute(
            f"UPDATE ideas SET {set_clause} WHERE id = ?",
            values,
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,))
        row = await cursor.fetchone()
        return _row_to_idea(row)
    finally:
        await db.close()


@router.delete("/{idea_id}", status_code=204)
async def delete_idea(idea_id: str):
    """Delete an idea."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Idea not found")

        await db.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
        await db.commit()
    finally:
        await db.close()


@router.post("/{idea_id}/refine")
async def refine_idea(idea_id: str, background_tasks: BackgroundTasks):
    """Start the refinement process for an idea."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Idea not found")

        if row["status"] not in ("pending", "questions"):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot refine idea in '{row['status']}' status"
            )

        await db.execute(
            "UPDATE ideas SET status = 'refining', updated_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), idea_id),
        )
        await db.commit()

        idea = _row_to_idea(row)
        idea.status = "refining"

        background_tasks.add_task(_run_refinement, idea)

        return {"message": "Refinement started", "idea_id": idea_id}
    finally:
        await db.close()


@router.post("/{idea_id}/approve")
async def approve_idea(idea_id: str):
    """Approve an idea and convert it to a ticket."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Idea not found")

        if row["status"] not in ("refining", "questions", "pending"):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot approve idea in '{row['status']}' status"
            )

        cursor = await db.execute(
            """
            SELECT q.question, q.answer, q.context
            FROM questions q WHERE q.idea_id = ? AND q.status = 'answered'
            """,
            (idea_id,),
        )
        answered_questions = [dict(q) for q in await cursor.fetchall()]

        ticket_id = generate_id()
        spec = {
            "original_idea": {
                "title": row["title"],
                "description": row["description"],
            },
            "answered_questions": answered_questions,
            "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
        }

        await db.execute(
            """
            INSERT INTO tickets (id, project_id, idea_id, title, description, type, priority, spec)
            VALUES (?, ?, ?, ?, ?, 'feature', ?, ?)
            """,
            (
                ticket_id,
                row["project_id"],
                idea_id,
                row["title"],
                row["description"],
                row["priority"],
                json.dumps(spec),
            ),
        )

        now = datetime.utcnow().isoformat()
        await db.execute(
            "UPDATE ideas SET status = 'converted', updated_at = ? WHERE id = ?",
            (now, idea_id),
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        ticket_row = await cursor.fetchone()

        return {
            "message": "Idea approved and converted to ticket",
            "ticket_id": ticket_id,
            "ticket": _row_to_ticket(ticket_row),
        }
    finally:
        await db.close()


@router.post("/{idea_id}/reject")
async def reject_idea(idea_id: str, reason: Optional[str] = None):
    """Reject an idea."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Idea not found")

        if row["status"] in ("converted", "rejected"):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot reject idea in '{row['status']}' status"
            )

        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        metadata["rejection_reason"] = reason

        await db.execute(
            "UPDATE ideas SET status = 'rejected', metadata = ?, updated_at = ? WHERE id = ?",
            (json.dumps(metadata), datetime.utcnow().isoformat(), idea_id),
        )
        await db.commit()

        return {"message": "Idea rejected", "idea_id": idea_id}
    finally:
        await db.close()


@router.get("/{idea_id}/questions", response_model=list[Question])
async def get_idea_questions(idea_id: str):
    """Get all questions for an idea."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Idea not found")

        cursor = await db.execute(
            "SELECT * FROM questions WHERE idea_id = ? ORDER BY created_at ASC",
            (idea_id,),
        )
        rows = await cursor.fetchall()
        return [_row_to_question(row) for row in rows]
    finally:
        await db.close()


async def _run_refinement(idea: Idea):
    """Background task to run refinement agents on an idea."""
    from agents.clarifier import clarify_idea, get_clarifier_agent
    from agents import AgentRuntime

    db = await get_db()
    try:
        try:
            runtime = AgentRuntime()
        except ValueError:
            await db.execute(
                "UPDATE ideas SET status = 'pending', updated_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), idea.id),
            )
            await db.commit()
            return

        result = await clarify_idea(idea, runtime)

        if result.get("error"):
            await db.execute(
                "UPDATE ideas SET status = 'pending', updated_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), idea.id),
            )
            await db.commit()
            return

        agent = get_clarifier_agent(idea.project_id)
        cursor = await db.execute(
            "SELECT id FROM agents WHERE id = ?", (agent.id,)
        )
        if not await cursor.fetchone():
            await db.execute(
                """
                INSERT INTO agents (id, project_id, name, description, type, prompt, model, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (agent.id, agent.project_id, agent.name, agent.description, agent.type, agent.prompt, agent.model),
            )

        questions = result.get("questions", [])
        for q in questions:
            q_id = generate_id()
            await db.execute(
                """
                INSERT INTO questions (id, idea_id, agent_id, question, context)
                VALUES (?, ?, ?, ?, ?)
                """,
                (q_id, idea.id, agent.id, q["question"], q.get("context")),
            )

        new_status = "questions" if questions else "approved"
        await db.execute(
            "UPDATE ideas SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, datetime.utcnow().isoformat(), idea.id),
        )
        await db.commit()
    finally:
        await db.close()


def _row_to_idea(row: aiosqlite.Row) -> Idea:
    """Convert database row to Idea model."""
    metadata = json.loads(row["metadata"]) if row["metadata"] else None
    return Idea(
        id=row["id"],
        project_id=row["project_id"],
        title=row["title"],
        description=row["description"],
        source=row["source"],
        status=row["status"],
        priority=row["priority"],
        metadata=metadata,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_ticket(row: aiosqlite.Row) -> Ticket:
    """Convert database row to Ticket model."""
    spec = json.loads(row["spec"]) if row["spec"] else None
    result = json.loads(row["result"]) if row["result"] else None
    return Ticket(
        id=row["id"],
        project_id=row["project_id"],
        idea_id=row["idea_id"],
        title=row["title"],
        description=row["description"],
        type=row["type"],
        status=row["status"],
        priority=row["priority"],
        assigned_agent=row["assigned_agent"],
        spec=spec,
        result=result,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        completed_at=row["completed_at"],
    )


def _row_to_question(row: aiosqlite.Row) -> Question:
    """Convert database row to Question model."""
    return Question(
        id=row["id"],
        idea_id=row["idea_id"],
        agent_id=row["agent_id"],
        question=row["question"],
        context=row["context"],
        answer=row["answer"],
        status=row["status"],
        created_at=row["created_at"],
        answered_at=row["answered_at"],
    )
