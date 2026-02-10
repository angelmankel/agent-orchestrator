"""Project CRUD endpoints."""

import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
import aiosqlite

from database import get_db
from models import Project, ProjectCreate, ProjectUpdate
from models.base import generate_id

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[Project])
async def list_projects():
    """List all projects."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM projects ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        projects = []
        for row in rows:
            projects.append(_row_to_project(row))
        return projects
    finally:
        await db.close()


@router.post("", response_model=Project, status_code=201)
async def create_project(project: ProjectCreate):
    """Create a new project."""
    db = await get_db()
    try:
        project_id = generate_id()
        config_json = json.dumps(project.config) if project.config else None

        await db.execute(
            """
            INSERT INTO projects (id, name, description, path, config)
            VALUES (?, ?, ?, ?, ?)
            """,
            (project_id, project.name, project.description, project.path, config_json),
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = await cursor.fetchone()
        return _row_to_project(row)
    finally:
        await db.close()


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Get a project by ID."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")
        return _row_to_project(row)
    finally:
        await db.close()


@router.patch("/{project_id}", response_model=Project)
async def update_project(project_id: str, updates: ProjectUpdate):
    """Update a project."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")

        update_data = updates.model_dump(exclude_unset=True)
        if not update_data:
            return _row_to_project(row)

        if "config" in update_data:
            update_data["config"] = json.dumps(update_data["config"])

        update_data["updated_at"] = datetime.utcnow().isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in update_data.keys())
        values = list(update_data.values()) + [project_id]

        await db.execute(
            f"UPDATE projects SET {set_clause} WHERE id = ?",
            values,
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = await cursor.fetchone()
        return _row_to_project(row)
    finally:
        await db.close()


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str):
    """Delete a project."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")

        await db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        await db.commit()
    finally:
        await db.close()


def _row_to_project(row: aiosqlite.Row) -> Project:
    """Convert database row to Project model."""
    config = json.loads(row["config"]) if row["config"] else None
    return Project(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        path=row["path"],
        config=config,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
