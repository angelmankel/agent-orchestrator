# Data Models

> **Status**: Draft
> **Last Updated**: 2026-02-05
> **Owner**: -
> **Depends On**: [01-architecture](01-architecture.md)

---

## Overview

SQLite database schema for the Agent Orchestrator. Defines all tables, relationships, and indexes needed to store projects, ideas, tickets, agents, and execution history.

---

## Goals

- [ ] Define normalized schema for all core entities
- [ ] Enable fast queries for common operations
- [ ] Support audit trail and history tracking
- [ ] Keep schema simple and extensible

---

## Non-Goals

- Multi-database support (SQLite only)
- Sharding or partitioning (single-file simplicity)
- Real-time sync (async updates are fine)

---

## Design

### Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Project   │──────<│    Idea     │──────<│  Question   │
└─────────────┘       └──────┬──────┘       └─────────────┘
       │                     │
       │                     ▼
       │              ┌─────────────┐       ┌─────────────┐
       │              │   Ticket    │──────<│  Subtask    │
       │              └──────┬──────┘       └─────────────┘
       │                     │
       ▼                     ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    Agent    │──────<│  Agent Run  │──────<│  Run Log    │
└─────────────┘       └─────────────┘       └─────────────┘
       │
       ▼
┌─────────────┐
│  Job Queue  │
└─────────────┘
```

### Core Tables

#### projects
Central table for all managed projects.

```sql
CREATE TABLE projects (
    id              TEXT PRIMARY KEY,  -- UUID
    name            TEXT NOT NULL,
    description     TEXT,
    path            TEXT NOT NULL,     -- filesystem path to project
    config          TEXT,              -- JSON blob for project settings
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_projects_name ON projects(name);
```

#### ideas
Raw ideas submitted for refinement.

```sql
CREATE TABLE ideas (
    id              TEXT PRIMARY KEY,  -- UUID
    project_id      TEXT NOT NULL REFERENCES projects(id),
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    source          TEXT,              -- 'web', 'api', 'cli'
    status          TEXT NOT NULL DEFAULT 'pending',
                    -- pending, refining, questions, approved, rejected, converted
    priority        INTEGER DEFAULT 0,
    metadata        TEXT,              -- JSON blob
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ideas_project ON ideas(project_id);
CREATE INDEX idx_ideas_status ON ideas(status);
```

#### questions
Clarifying questions from agents, awaiting human response.

```sql
CREATE TABLE questions (
    id              TEXT PRIMARY KEY,  -- UUID
    idea_id         TEXT NOT NULL REFERENCES ideas(id),
    agent_id        TEXT NOT NULL REFERENCES agents(id),
    question        TEXT NOT NULL,
    context         TEXT,              -- why the agent is asking
    answer          TEXT,              -- human response
    status          TEXT NOT NULL DEFAULT 'pending',
                    -- pending, answered, skipped
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    answered_at     DATETIME
);

CREATE INDEX idx_questions_idea ON questions(idea_id);
CREATE INDEX idx_questions_status ON questions(status);
```

#### tickets
Approved ideas ready for development.

```sql
CREATE TABLE tickets (
    id              TEXT PRIMARY KEY,  -- UUID
    project_id      TEXT NOT NULL REFERENCES projects(id),
    idea_id         TEXT REFERENCES ideas(id),  -- nullable for manual tickets
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    type            TEXT NOT NULL,     -- 'feature', 'bugfix', 'refactor', 'chore'
    status          TEXT NOT NULL DEFAULT 'queued',
                    -- queued, in_progress, review, blocked, done, cancelled
    priority        INTEGER DEFAULT 0,
    assigned_agent  TEXT REFERENCES agents(id),
    spec            TEXT,              -- JSON blob: detailed specification
    result          TEXT,              -- JSON blob: implementation summary
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at    DATETIME
);

CREATE INDEX idx_tickets_project ON tickets(project_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_priority ON tickets(priority DESC);
```

#### subtasks
Breakdown of tickets into smaller units.

```sql
CREATE TABLE subtasks (
    id              TEXT PRIMARY KEY,  -- UUID
    ticket_id       TEXT NOT NULL REFERENCES tickets(id),
    title           TEXT NOT NULL,
    description     TEXT,
    status          TEXT NOT NULL DEFAULT 'pending',
                    -- pending, in_progress, done, skipped
    order_index     INTEGER DEFAULT 0,
    agent_id        TEXT REFERENCES agents(id),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at    DATETIME
);

CREATE INDEX idx_subtasks_ticket ON subtasks(ticket_id);
```

#### agents
Agent definitions and configuration.

```sql
CREATE TABLE agents (
    id              TEXT PRIMARY KEY,  -- UUID
    project_id      TEXT REFERENCES projects(id),  -- null = global agent
    name            TEXT NOT NULL,
    description     TEXT NOT NULL,
    type            TEXT NOT NULL,     -- 'refinement', 'development', 'support', 'planning'
    prompt          TEXT NOT NULL,     -- system prompt
    tools           TEXT,              -- JSON array of allowed tools
    model           TEXT DEFAULT 'sonnet',
    config          TEXT,              -- JSON blob for additional settings
    is_active       BOOLEAN DEFAULT 1,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agents_project ON agents(project_id);
CREATE INDEX idx_agents_type ON agents(type);
CREATE UNIQUE INDEX idx_agents_name_project ON agents(name, project_id);
```

#### agent_runs
Execution history for agents.

```sql
CREATE TABLE agent_runs (
    id              TEXT PRIMARY KEY,  -- UUID
    agent_id        TEXT NOT NULL REFERENCES agents(id),
    ticket_id       TEXT REFERENCES tickets(id),
    idea_id         TEXT REFERENCES ideas(id),
    status          TEXT NOT NULL DEFAULT 'running',
                    -- running, success, failed, cancelled
    input           TEXT,              -- JSON: what was passed to agent
    output          TEXT,              -- JSON: what agent returned
    tokens_used     INTEGER DEFAULT 0,
    cost_usd        REAL DEFAULT 0,
    started_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at    DATETIME,
    error           TEXT
);

CREATE INDEX idx_agent_runs_agent ON agent_runs(agent_id);
CREATE INDEX idx_agent_runs_ticket ON agent_runs(ticket_id);
CREATE INDEX idx_agent_runs_status ON agent_runs(status);
```

#### run_logs
Detailed logs for each agent run.

```sql
CREATE TABLE run_logs (
    id              TEXT PRIMARY KEY,  -- UUID
    run_id          TEXT NOT NULL REFERENCES agent_runs(id),
    level           TEXT NOT NULL,     -- 'debug', 'info', 'warn', 'error'
    message         TEXT NOT NULL,
    data            TEXT,              -- JSON blob for structured data
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_run_logs_run ON run_logs(run_id);
CREATE INDEX idx_run_logs_level ON run_logs(level);
```

#### job_queue
Async job queue backed by SQLite.

```sql
CREATE TABLE job_queue (
    id              TEXT PRIMARY KEY,  -- UUID
    job_type        TEXT NOT NULL,     -- 'refine_idea', 'develop_ticket', etc.
    payload         TEXT NOT NULL,     -- JSON blob
    status          TEXT NOT NULL DEFAULT 'pending',
                    -- pending, running, done, failed, cancelled
    priority        INTEGER DEFAULT 0,
    attempts        INTEGER DEFAULT 0,
    max_attempts    INTEGER DEFAULT 3,
    scheduled_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at      DATETIME,
    completed_at    DATETIME,
    error           TEXT,
    result          TEXT               -- JSON blob
);

CREATE INDEX idx_job_queue_status ON job_queue(status);
CREATE INDEX idx_job_queue_scheduled ON job_queue(scheduled_at);
CREATE INDEX idx_job_queue_priority ON job_queue(priority DESC);
```

#### users
User accounts (for auth).

```sql
CREATE TABLE users (
    id              TEXT PRIMARY KEY,  -- UUID
    username        TEXT NOT NULL UNIQUE,
    email           TEXT UNIQUE,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'user',  -- 'admin', 'user'
    is_active       BOOLEAN DEFAULT 1,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login      DATETIME
);
```

#### sessions
User sessions for auth.

```sql
CREATE TABLE sessions (
    id              TEXT PRIMARY KEY,  -- UUID
    user_id         TEXT NOT NULL REFERENCES users(id),
    token           TEXT NOT NULL UNIQUE,
    expires_at      DATETIME NOT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_token ON sessions(token);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
```

#### usage_tracking
Token and cost tracking.

```sql
CREATE TABLE usage_tracking (
    id              TEXT PRIMARY KEY,  -- UUID
    project_id      TEXT REFERENCES projects(id),
    agent_id        TEXT REFERENCES agents(id),
    run_id          TEXT REFERENCES agent_runs(id),
    tokens_input    INTEGER DEFAULT 0,
    tokens_output   INTEGER DEFAULT 0,
    cost_usd        REAL DEFAULT 0,
    model           TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_usage_project ON usage_tracking(project_id);
CREATE INDEX idx_usage_created ON usage_tracking(created_at);
```

---

## Common Queries

### Get pending ideas with unanswered questions
```sql
SELECT i.*, COUNT(q.id) as pending_questions
FROM ideas i
LEFT JOIN questions q ON q.idea_id = i.id AND q.status = 'pending'
WHERE i.status = 'questions'
GROUP BY i.id;
```

### Get development queue ordered by priority
```sql
SELECT t.*, a.name as agent_name
FROM tickets t
LEFT JOIN agents a ON t.assigned_agent = a.id
WHERE t.status IN ('queued', 'in_progress')
ORDER BY t.priority DESC, t.created_at ASC;
```

### Get usage summary by project
```sql
SELECT
    p.name,
    SUM(u.tokens_input + u.tokens_output) as total_tokens,
    SUM(u.cost_usd) as total_cost
FROM usage_tracking u
JOIN projects p ON u.project_id = p.id
GROUP BY p.id
ORDER BY total_cost DESC;
```

---

## Open Questions

| Question | Context | Decision |
|----------|---------|----------|
| Soft delete vs hard delete? | Data retention | TBD - lean toward soft delete with `deleted_at` |
| JSON vs normalized for config? | Flexibility vs queryability | TBD - JSON for now, normalize if needed |
| Separate DB per project? | Isolation | TBD - single DB simpler, separate more portable |

---

## Dependencies

- **Depends on**: 01-architecture
- **Depended by**: 03-agent-system, 04-ideas-pipeline, 05-development-pipeline, 07-api-design

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-02-05 | Initial draft | - |
