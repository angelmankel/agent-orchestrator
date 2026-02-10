"""Question CRUD and Q&A flow endpoints."""

import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
import aiosqlite

from database import get_db
from models import Question, QuestionCreate, QuestionAnswer
from models.base import generate_id

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("", response_model=list[Question])
async def list_questions(
    idea_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """List questions with optional filtering."""
    db = await get_db()
    try:
        query = "SELECT * FROM questions WHERE 1=1"
        params = []

        if idea_id:
            query += " AND idea_id = ?"
            params.append(idea_id)
        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at ASC"

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [_row_to_question(row) for row in rows]
    finally:
        await db.close()


@router.get("/pending", response_model=list[Question])
async def list_pending_questions(project_id: Optional[str] = Query(None)):
    """List all pending questions, optionally filtered by project."""
    db = await get_db()
    try:
        if project_id:
            query = """
                SELECT q.* FROM questions q
                JOIN ideas i ON q.idea_id = i.id
                WHERE q.status = 'pending' AND i.project_id = ?
                ORDER BY q.created_at ASC
            """
            cursor = await db.execute(query, (project_id,))
        else:
            query = "SELECT * FROM questions WHERE status = 'pending' ORDER BY created_at ASC"
            cursor = await db.execute(query)

        rows = await cursor.fetchall()
        return [_row_to_question(row) for row in rows]
    finally:
        await db.close()


@router.post("", response_model=Question, status_code=201)
async def create_question(question: QuestionCreate):
    """Create a new question."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id FROM ideas WHERE id = ?", (question.idea_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Idea not found")

        cursor = await db.execute(
            "SELECT id FROM agents WHERE id = ?", (question.agent_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Agent not found")

        question_id = generate_id()

        await db.execute(
            """
            INSERT INTO questions (id, idea_id, agent_id, question, context)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                question_id,
                question.idea_id,
                question.agent_id,
                question.question,
                question.context,
            ),
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
        row = await cursor.fetchone()
        return _row_to_question(row)
    finally:
        await db.close()


@router.get("/{question_id}", response_model=Question)
async def get_question(question_id: str):
    """Get a question by ID."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Question not found")
        return _row_to_question(row)
    finally:
        await db.close()


@router.post("/{question_id}/answer", response_model=Question)
async def answer_question(question_id: str, answer_data: QuestionAnswer):
    """Answer a question and trigger re-refinement if all questions answered."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Question not found")

        if row["status"] != "pending":
            raise HTTPException(status_code=400, detail="Question already answered")

        now = datetime.utcnow().isoformat()
        await db.execute(
            """
            UPDATE questions
            SET answer = ?, status = 'answered', answered_at = ?
            WHERE id = ?
            """,
            (answer_data.answer, now, question_id),
        )

        idea_id = row["idea_id"]

        cursor = await db.execute(
            "SELECT COUNT(*) as count FROM questions WHERE idea_id = ? AND status = 'pending'",
            (idea_id,),
        )
        pending_count = (await cursor.fetchone())["count"]

        if pending_count == 0:
            await db.execute(
                "UPDATE ideas SET status = 'refining', updated_at = ? WHERE id = ?",
                (now, idea_id),
            )

        await db.commit()

        cursor = await db.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
        row = await cursor.fetchone()
        return _row_to_question(row)
    finally:
        await db.close()


@router.post("/{question_id}/skip", response_model=Question)
async def skip_question(question_id: str):
    """Skip a question."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Question not found")

        if row["status"] != "pending":
            raise HTTPException(status_code=400, detail="Question already processed")

        now = datetime.utcnow().isoformat()
        await db.execute(
            """
            UPDATE questions SET status = 'skipped', answered_at = ? WHERE id = ?
            """,
            (now, question_id),
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
        row = await cursor.fetchone()
        return _row_to_question(row)
    finally:
        await db.close()


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
