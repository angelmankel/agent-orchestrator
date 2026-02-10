"""Ticket CRUD and development pipeline endpoints."""

import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
import aiosqlite

from database import get_db
from models import Ticket, TicketCreate, TicketUpdate, Subtask, SubtaskCreate, SubtaskUpdate
from models.base import generate_id

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=list[Ticket])
async def list_tickets(
    project_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    assigned_agent: Optional[str] = Query(None),
):
    """List tickets with optional filtering."""
    db = await get_db()
    try:
        query = "SELECT * FROM tickets WHERE 1=1"
        params = []

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        if type:
            query += " AND type = ?"
            params.append(type)
        if assigned_agent:
            query += " AND assigned_agent = ?"
            params.append(assigned_agent)

        query += " ORDER BY priority DESC, created_at ASC"

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [_row_to_ticket(row) for row in rows]
    finally:
        await db.close()


@router.get("/queue", response_model=list[Ticket])
async def get_ticket_queue(project_id: Optional[str] = Query(None)):
    """Get the development queue (queued and in_progress tickets)."""
    db = await get_db()
    try:
        query = """
            SELECT * FROM tickets
            WHERE status IN ('queued', 'in_progress', 'review', 'blocked')
        """
        params = []

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)

        query += " ORDER BY priority DESC, created_at ASC"

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [_row_to_ticket(row) for row in rows]
    finally:
        await db.close()


@router.post("", response_model=Ticket, status_code=201)
async def create_ticket(ticket: TicketCreate):
    """Create a new ticket."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id FROM projects WHERE id = ?", (ticket.project_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")

        if ticket.idea_id:
            cursor = await db.execute(
                "SELECT id FROM ideas WHERE id = ?", (ticket.idea_id,)
            )
            if not await cursor.fetchone():
                raise HTTPException(status_code=404, detail="Idea not found")

        if ticket.assigned_agent:
            cursor = await db.execute(
                "SELECT id FROM agents WHERE id = ?", (ticket.assigned_agent,)
            )
            if not await cursor.fetchone():
                raise HTTPException(status_code=404, detail="Agent not found")

        ticket_id = generate_id()
        spec_json = json.dumps(ticket.spec) if ticket.spec else None

        await db.execute(
            """
            INSERT INTO tickets (id, project_id, idea_id, title, description, type, priority, assigned_agent, spec)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                ticket.project_id,
                ticket.idea_id,
                ticket.title,
                ticket.description,
                ticket.type,
                ticket.priority,
                ticket.assigned_agent,
                spec_json,
            ),
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = await cursor.fetchone()
        return _row_to_ticket(row)
    finally:
        await db.close()


@router.get("/{ticket_id}", response_model=Ticket)
async def get_ticket(ticket_id: str):
    """Get a ticket by ID."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return _row_to_ticket(row)
    finally:
        await db.close()


@router.patch("/{ticket_id}", response_model=Ticket)
async def update_ticket(ticket_id: str, updates: TicketUpdate):
    """Update a ticket."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")

        update_data = updates.model_dump(exclude_unset=True)
        if not update_data:
            return _row_to_ticket(row)

        if "spec" in update_data:
            update_data["spec"] = json.dumps(update_data["spec"])
        if "result" in update_data:
            update_data["result"] = json.dumps(update_data["result"])

        if update_data.get("status") == "done" and row["status"] != "done":
            update_data["completed_at"] = datetime.utcnow().isoformat()

        update_data["updated_at"] = datetime.utcnow().isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in update_data.keys())
        values = list(update_data.values()) + [ticket_id]

        await db.execute(
            f"UPDATE tickets SET {set_clause} WHERE id = ?",
            values,
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = await cursor.fetchone()
        return _row_to_ticket(row)
    finally:
        await db.close()


@router.delete("/{ticket_id}", status_code=204)
async def delete_ticket(ticket_id: str):
    """Delete a ticket."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")

        await db.execute("DELETE FROM subtasks WHERE ticket_id = ?", (ticket_id,))
        await db.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
        await db.commit()
    finally:
        await db.close()


@router.post("/{ticket_id}/start")
async def start_ticket(ticket_id: str, background_tasks: BackgroundTasks):
    """Start working on a ticket (moves to in_progress)."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")

        if row["status"] != "queued":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot start ticket in '{row['status']}' status"
            )

        await db.execute(
            "UPDATE tickets SET status = 'in_progress', updated_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), ticket_id),
        )
        await db.commit()

        ticket = _row_to_ticket(row)
        ticket.status = "in_progress"
        background_tasks.add_task(_run_development, ticket)

        return {"message": "Ticket started", "ticket_id": ticket_id}
    finally:
        await db.close()


@router.post("/{ticket_id}/review")
async def submit_for_review(ticket_id: str):
    """Submit a ticket for human review."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")

        if row["status"] != "in_progress":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot submit for review from '{row['status']}' status"
            )

        await db.execute(
            "UPDATE tickets SET status = 'review', updated_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), ticket_id),
        )
        await db.commit()

        return {"message": "Ticket submitted for review", "ticket_id": ticket_id}
    finally:
        await db.close()


@router.get("/{ticket_id}/review")
async def get_review_summary(ticket_id: str):
    """Get review summary for a ticket."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")

        cursor = await db.execute(
            "SELECT * FROM subtasks WHERE ticket_id = ? ORDER BY order_index ASC",
            (ticket_id,),
        )
        subtasks = [_row_to_subtask(s) for s in await cursor.fetchall()]

        cursor = await db.execute(
            """
            SELECT ar.* FROM agent_runs ar
            WHERE ar.ticket_id = ?
            ORDER BY ar.started_at DESC
            """,
            (ticket_id,),
        )
        runs = await cursor.fetchall()

        build_results = []
        test_results = []
        review_results = []

        for run in runs:
            output = json.loads(run["output"]) if run["output"] else {}
            run_type = output.get("type")
            if run_type == "build":
                build_results.append(output)
            elif run_type == "test":
                test_results.append(output)
            elif run_type == "review":
                review_results.append(output)

        return {
            "ticket": _row_to_ticket(row),
            "subtasks": subtasks,
            "build_results": build_results[:5],
            "test_results": test_results[:5],
            "review_results": review_results[:5],
            "total_runs": len(runs),
        }
    finally:
        await db.close()


@router.post("/{ticket_id}/approve")
async def approve_ticket(ticket_id: str, comment: Optional[str] = None):
    """Approve a ticket and mark as done."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")

        if row["status"] != "review":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot approve ticket in '{row['status']}' status"
            )

        result = json.loads(row["result"]) if row["result"] else {}
        result["approval"] = {
            "approved_at": datetime.utcnow().isoformat(),
            "comment": comment,
        }

        now = datetime.utcnow().isoformat()
        await db.execute(
            """
            UPDATE tickets SET status = 'done', result = ?, updated_at = ?, completed_at = ?
            WHERE id = ?
            """,
            (json.dumps(result), now, now, ticket_id),
        )
        await db.commit()

        return {"message": "Ticket approved", "ticket_id": ticket_id}
    finally:
        await db.close()


@router.post("/{ticket_id}/request-changes")
async def request_changes(ticket_id: str, feedback: str):
    """Request changes on a ticket (returns to in_progress)."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")

        if row["status"] != "review":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot request changes on ticket in '{row['status']}' status"
            )

        result = json.loads(row["result"]) if row["result"] else {}
        if "change_requests" not in result:
            result["change_requests"] = []
        result["change_requests"].append({
            "requested_at": datetime.utcnow().isoformat(),
            "feedback": feedback,
        })

        await db.execute(
            """
            UPDATE tickets SET status = 'in_progress', result = ?, updated_at = ?
            WHERE id = ?
            """,
            (json.dumps(result), datetime.utcnow().isoformat(), ticket_id),
        )
        await db.commit()

        return {"message": "Changes requested", "ticket_id": ticket_id, "feedback": feedback}
    finally:
        await db.close()


@router.post("/{ticket_id}/cancel")
async def cancel_ticket(ticket_id: str, reason: Optional[str] = None):
    """Cancel a ticket."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")

        if row["status"] in ("done", "cancelled"):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel ticket in '{row['status']}' status"
            )

        result = json.loads(row["result"]) if row["result"] else {}
        result["cancellation"] = {
            "cancelled_at": datetime.utcnow().isoformat(),
            "reason": reason,
        }

        await db.execute(
            """
            UPDATE tickets SET status = 'cancelled', result = ?, updated_at = ?
            WHERE id = ?
            """,
            (json.dumps(result), datetime.utcnow().isoformat(), ticket_id),
        )
        await db.commit()

        return {"message": "Ticket cancelled", "ticket_id": ticket_id}
    finally:
        await db.close()


# Subtask endpoints

@router.get("/{ticket_id}/subtasks", response_model=list[Subtask])
async def list_subtasks(ticket_id: str):
    """List subtasks for a ticket."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Ticket not found")

        cursor = await db.execute(
            "SELECT * FROM subtasks WHERE ticket_id = ? ORDER BY order_index ASC",
            (ticket_id,),
        )
        rows = await cursor.fetchall()
        return [_row_to_subtask(row) for row in rows]
    finally:
        await db.close()


@router.post("/{ticket_id}/subtasks", response_model=Subtask, status_code=201)
async def create_subtask(ticket_id: str, subtask: SubtaskCreate):
    """Create a subtask for a ticket."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Ticket not found")

        subtask_id = generate_id()

        await db.execute(
            """
            INSERT INTO subtasks (id, ticket_id, title, description, order_index, agent_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                subtask_id,
                ticket_id,
                subtask.title,
                subtask.description,
                subtask.order_index,
                subtask.agent_id,
            ),
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM subtasks WHERE id = ?", (subtask_id,))
        row = await cursor.fetchone()
        return _row_to_subtask(row)
    finally:
        await db.close()


@router.patch("/{ticket_id}/subtasks/{subtask_id}", response_model=Subtask)
async def update_subtask(ticket_id: str, subtask_id: str, updates: SubtaskUpdate):
    """Update a subtask."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM subtasks WHERE id = ? AND ticket_id = ?",
            (subtask_id, ticket_id),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Subtask not found")

        update_data = updates.model_dump(exclude_unset=True)
        if not update_data:
            return _row_to_subtask(row)

        if update_data.get("status") == "done" and row["status"] != "done":
            update_data["completed_at"] = datetime.utcnow().isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in update_data.keys())
        values = list(update_data.values()) + [subtask_id]

        await db.execute(
            f"UPDATE subtasks SET {set_clause} WHERE id = ?",
            values,
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM subtasks WHERE id = ?", (subtask_id,))
        row = await cursor.fetchone()
        return _row_to_subtask(row)
    finally:
        await db.close()


async def _run_development(ticket: Ticket):
    """Background task to run development agents on a ticket."""
    from agents.developer import develop_ticket

    try:
        await develop_ticket(ticket)
    except Exception as e:
        db = await get_db()
        try:
            result = {"error": str(e)}
            await db.execute(
                """
                UPDATE tickets SET status = 'blocked', result = ?, updated_at = ?
                WHERE id = ?
                """,
                (json.dumps(result), datetime.utcnow().isoformat(), ticket.id),
            )
            await db.commit()
        finally:
            await db.close()


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


def _row_to_subtask(row: aiosqlite.Row) -> Subtask:
    """Convert database row to Subtask model."""
    return Subtask(
        id=row["id"],
        ticket_id=row["ticket_id"],
        title=row["title"],
        description=row["description"],
        status=row["status"],
        order_index=row["order_index"],
        agent_id=row["agent_id"],
        created_at=row["created_at"],
        completed_at=row["completed_at"],
    )
