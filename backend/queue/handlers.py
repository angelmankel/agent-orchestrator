"""Job handlers for async processing."""

import json
import logging
from datetime import datetime

from database import get_db
from models import Idea
from models.base import generate_id
from agents import AgentRuntime
from agents.clarifier import clarify_idea, get_clarifier_agent

logger = logging.getLogger(__name__)


async def handle_refine_idea(payload: dict) -> dict:
    """
    Handle idea refinement job.

    Payload:
        idea_id: str - The idea to refine

    Returns:
        Dict with refinement results
    """
    idea_id = payload.get("idea_id")
    if not idea_id:
        raise ValueError("Missing idea_id in payload")

    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,))
        row = await cursor.fetchone()
        if not row:
            raise ValueError(f"Idea {idea_id} not found")

        idea = Idea(
            id=row["id"],
            project_id=row["project_id"],
            title=row["title"],
            description=row["description"],
            source=row["source"],
            status=row["status"],
            priority=row["priority"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else None,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

        try:
            runtime = AgentRuntime()
        except ValueError as e:
            logger.error(f"Cannot create AgentRuntime: {e}")
            return {"error": str(e), "idea_id": idea_id}

        result = await clarify_idea(idea, runtime)

        if result.get("error"):
            await db.execute(
                "UPDATE ideas SET status = 'pending', updated_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), idea_id),
            )
            await db.commit()
            return {"error": result["error"], "idea_id": idea_id}

        agent = get_clarifier_agent(idea.project_id)
        cursor = await db.execute("SELECT id FROM agents WHERE id = ?", (agent.id,))
        if not await cursor.fetchone():
            await db.execute(
                """
                INSERT INTO agents (id, project_id, name, description, type, prompt, model, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (agent.id, agent.project_id, agent.name, agent.description, agent.type, agent.prompt, agent.model),
            )

        questions = result.get("questions", [])
        question_ids = []
        for q in questions:
            q_id = generate_id()
            question_ids.append(q_id)
            await db.execute(
                """
                INSERT INTO questions (id, idea_id, agent_id, question, context)
                VALUES (?, ?, ?, ?, ?)
                """,
                (q_id, idea_id, agent.id, q["question"], q.get("context")),
            )

        new_status = "questions" if questions else "approved"
        await db.execute(
            "UPDATE ideas SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, datetime.utcnow().isoformat(), idea_id),
        )
        await db.commit()

        return {
            "idea_id": idea_id,
            "status": new_status,
            "questions_created": len(questions),
            "question_ids": question_ids,
            "analysis": result.get("analysis"),
        }

    finally:
        await db.close()


async def handle_convert_idea(payload: dict) -> dict:
    """
    Handle idea to ticket conversion job.

    Payload:
        idea_id: str - The idea to convert

    Returns:
        Dict with ticket info
    """
    idea_id = payload.get("idea_id")
    if not idea_id:
        raise ValueError("Missing idea_id in payload")

    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,))
        row = await cursor.fetchone()
        if not row:
            raise ValueError(f"Idea {idea_id} not found")

        if row["status"] == "converted":
            cursor = await db.execute(
                "SELECT id FROM tickets WHERE idea_id = ?", (idea_id,)
            )
            ticket_row = await cursor.fetchone()
            return {"idea_id": idea_id, "ticket_id": ticket_row["id"] if ticket_row else None}

        cursor = await db.execute(
            "SELECT question, answer, context FROM questions WHERE idea_id = ? AND status = 'answered'",
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

        await db.execute(
            "UPDATE ideas SET status = 'converted', updated_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), idea_id),
        )
        await db.commit()

        return {"idea_id": idea_id, "ticket_id": ticket_id}

    finally:
        await db.close()


def register_handlers(worker):
    """Register all job handlers with the worker."""
    worker.register("refine_idea", handle_refine_idea)
    worker.register("convert_idea", handle_convert_idea)
