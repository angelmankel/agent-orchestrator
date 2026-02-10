"""SQLite database setup and connection management."""

import aiosqlite
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / "data" / "orchestrator.db"

SCHEMA = """
-- Projects
CREATE TABLE IF NOT EXISTS projects (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    description     TEXT,
    path            TEXT NOT NULL,
    config          TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);

-- Ideas
CREATE TABLE IF NOT EXISTS ideas (
    id              TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL REFERENCES projects(id),
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    source          TEXT,
    status          TEXT NOT NULL DEFAULT 'pending',
    priority        INTEGER DEFAULT 0,
    metadata        TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_ideas_project ON ideas(project_id);
CREATE INDEX IF NOT EXISTS idx_ideas_status ON ideas(status);

-- Agents
CREATE TABLE IF NOT EXISTS agents (
    id              TEXT PRIMARY KEY,
    project_id      TEXT REFERENCES projects(id),
    name            TEXT NOT NULL,
    description     TEXT NOT NULL,
    type            TEXT NOT NULL,
    prompt          TEXT NOT NULL,
    tools           TEXT,
    model           TEXT DEFAULT 'sonnet',
    config          TEXT,
    is_active       INTEGER DEFAULT 1,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_agents_project ON agents(project_id);
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(type);

-- Questions
CREATE TABLE IF NOT EXISTS questions (
    id              TEXT PRIMARY KEY,
    idea_id         TEXT NOT NULL REFERENCES ideas(id),
    agent_id        TEXT NOT NULL REFERENCES agents(id),
    question        TEXT NOT NULL,
    context         TEXT,
    answer          TEXT,
    status          TEXT NOT NULL DEFAULT 'pending',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    answered_at     DATETIME
);
CREATE INDEX IF NOT EXISTS idx_questions_idea ON questions(idea_id);
CREATE INDEX IF NOT EXISTS idx_questions_status ON questions(status);

-- Tickets
CREATE TABLE IF NOT EXISTS tickets (
    id              TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL REFERENCES projects(id),
    idea_id         TEXT REFERENCES ideas(id),
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    type            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'queued',
    priority        INTEGER DEFAULT 0,
    assigned_agent  TEXT REFERENCES agents(id),
    spec            TEXT,
    result          TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at    DATETIME
);
CREATE INDEX IF NOT EXISTS idx_tickets_project ON tickets(project_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority DESC);

-- Subtasks
CREATE TABLE IF NOT EXISTS subtasks (
    id              TEXT PRIMARY KEY,
    ticket_id       TEXT NOT NULL REFERENCES tickets(id),
    title           TEXT NOT NULL,
    description     TEXT,
    status          TEXT NOT NULL DEFAULT 'pending',
    order_index     INTEGER DEFAULT 0,
    agent_id        TEXT REFERENCES agents(id),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at    DATETIME
);
CREATE INDEX IF NOT EXISTS idx_subtasks_ticket ON subtasks(ticket_id);

-- Agent Runs
CREATE TABLE IF NOT EXISTS agent_runs (
    id              TEXT PRIMARY KEY,
    agent_id        TEXT NOT NULL REFERENCES agents(id),
    ticket_id       TEXT REFERENCES tickets(id),
    idea_id         TEXT REFERENCES ideas(id),
    status          TEXT NOT NULL DEFAULT 'running',
    input           TEXT,
    output          TEXT,
    tokens_used     INTEGER DEFAULT 0,
    cost_usd        REAL DEFAULT 0,
    started_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at    DATETIME,
    error           TEXT
);
CREATE INDEX IF NOT EXISTS idx_agent_runs_agent ON agent_runs(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_ticket ON agent_runs(ticket_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON agent_runs(status);

-- Run Logs
CREATE TABLE IF NOT EXISTS run_logs (
    id              TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL REFERENCES agent_runs(id),
    level           TEXT NOT NULL,
    message         TEXT NOT NULL,
    data            TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_run_logs_run ON run_logs(run_id);
CREATE INDEX IF NOT EXISTS idx_run_logs_level ON run_logs(level);

-- Job Queue
CREATE TABLE IF NOT EXISTS job_queue (
    id              TEXT PRIMARY KEY,
    job_type        TEXT NOT NULL,
    payload         TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',
    priority        INTEGER DEFAULT 0,
    attempts        INTEGER DEFAULT 0,
    max_attempts    INTEGER DEFAULT 3,
    scheduled_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at      DATETIME,
    completed_at    DATETIME,
    error           TEXT,
    result          TEXT
);
CREATE INDEX IF NOT EXISTS idx_job_queue_status ON job_queue(status);
CREATE INDEX IF NOT EXISTS idx_job_queue_scheduled ON job_queue(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_job_queue_priority ON job_queue(priority DESC);

-- Users
CREATE TABLE IF NOT EXISTS users (
    id              TEXT PRIMARY KEY,
    username        TEXT NOT NULL UNIQUE,
    email           TEXT UNIQUE,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'user',
    is_active       INTEGER DEFAULT 1,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login      DATETIME
);

-- Sessions
CREATE TABLE IF NOT EXISTS sessions (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(id),
    token           TEXT NOT NULL UNIQUE,
    expires_at      DATETIME NOT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

-- Usage Tracking
CREATE TABLE IF NOT EXISTS usage_tracking (
    id              TEXT PRIMARY KEY,
    project_id      TEXT REFERENCES projects(id),
    agent_id        TEXT REFERENCES agents(id),
    run_id          TEXT REFERENCES agent_runs(id),
    tokens_input    INTEGER DEFAULT 0,
    tokens_output   INTEGER DEFAULT 0,
    cost_usd        REAL DEFAULT 0,
    model           TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_usage_project ON usage_tracking(project_id);
CREATE INDEX IF NOT EXISTS idx_usage_created ON usage_tracking(created_at);
"""


async def get_db() -> aiosqlite.Connection:
    """Get database connection."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    """Initialize database with schema."""
    db = await get_db()
    try:
        await db.executescript(SCHEMA)
        await db.commit()
    finally:
        await db.close()


async def close_db(db: aiosqlite.Connection):
    """Close database connection."""
    await db.close()
