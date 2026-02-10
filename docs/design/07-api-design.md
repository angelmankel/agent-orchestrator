# API Design

> **Status**: Draft
> **Last Updated**: 2026-02-05
> **Owner**: -
> **Depends On**: [01-architecture](01-architecture.md), [02-data-models](02-data-models.md)

---

## Overview

RESTful API design for the Agent Orchestrator. Covers all endpoints for projects, ideas, tickets, agents, and system operations.

---

## Goals

- [ ] Define consistent, intuitive REST endpoints
- [ ] Support all UI operations
- [ ] Enable third-party integrations
- [ ] Provide real-time status updates
- [ ] Include comprehensive error handling

---

## Non-Goals

- GraphQL (REST is sufficient)
- gRPC (not needed for this scale)
- Public API versioning (internal use first)

---

## Design

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
```
Authorization: Bearer <token>
```

All endpoints except `/auth/*` require authentication.

### Common Response Format

#### Success
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2026-02-05T10:30:00Z",
    "request_id": "uuid"
  }
}
```

#### Error
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Title is required",
    "details": { "field": "title" }
  },
  "meta": {
    "timestamp": "2026-02-05T10:30:00Z",
    "request_id": "uuid"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid input |
| `UNAUTHORIZED` | 401 | Not authenticated |
| `FORBIDDEN` | 403 | Not authorized |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

---

## Endpoints

### Authentication

#### POST /auth/login
```json
// Request
{
  "username": "string",
  "password": "string"
}

// Response
{
  "token": "jwt-token",
  "expires_at": "2026-02-06T10:30:00Z",
  "user": {
    "id": "uuid",
    "username": "string",
    "role": "admin"
  }
}
```

#### POST /auth/logout
```json
// Response
{ "success": true }
```

#### GET /auth/me
```json
// Response
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "role": "admin"
}
```

---

### Projects

#### GET /projects
List all projects.

```json
// Query params: ?status=active&limit=20&offset=0

// Response
{
  "items": [
    {
      "id": "uuid",
      "name": "My ARPG",
      "description": "...",
      "path": "/path/to/project",
      "created_at": "2026-01-15T...",
      "stats": {
        "ideas_pending": 5,
        "tickets_queued": 3,
        "tickets_in_progress": 1
      }
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### POST /projects
Create a new project.

```json
// Request
{
  "name": "My ARPG",
  "description": "An action RPG game",
  "path": "/path/to/project",
  "config": {
    "build_command": "make build",
    "test_command": "make test"
  }
}

// Response
{ "id": "uuid", "name": "My ARPG", ... }
```

#### GET /projects/:id
Get project details.

#### PATCH /projects/:id
Update project.

#### DELETE /projects/:id
Delete project (soft delete).

---

### Ideas

#### GET /projects/:projectId/ideas
List ideas for a project.

```json
// Query params: ?status=pending,questions&priority=high&limit=20

// Response
{
  "items": [
    {
      "id": "uuid",
      "title": "Add multiplayer",
      "description": "...",
      "status": "questions",
      "priority": 2,
      "pending_questions": 2,
      "created_at": "..."
    }
  ],
  "total": 5
}
```

#### POST /projects/:projectId/ideas
Submit a new idea.

```json
// Request
{
  "title": "Add multiplayer support",
  "description": "Players should be able to...",
  "priority": 0,
  "metadata": {
    "tags": ["multiplayer", "feature"]
  }
}

// Response
{ "id": "uuid", "status": "pending", ... }
```

#### GET /ideas/:id
Get idea details with questions and analysis.

```json
// Response
{
  "id": "uuid",
  "title": "Add multiplayer",
  "description": "...",
  "status": "questions",
  "analysis": {
    "related_files": ["src/network/"],
    "similar_features": ["chat-system"],
    "estimated_complexity": "high"
  },
  "questions": [
    {
      "id": "q-uuid",
      "question": "Shared or separate inventory?",
      "context": "...",
      "status": "pending",
      "answer": null
    }
  ],
  "subtasks": [
    { "title": "Network layer", "complexity": "high" }
  ]
}
```

#### PATCH /ideas/:id
Update idea (change status, priority).

#### POST /ideas/:id/approve
Approve idea and convert to ticket.

```json
// Request (optional overrides)
{
  "priority": 2,
  "assigned_agent": "feature-dev"
}

// Response
{
  "ticket": { "id": "ticket-uuid", ... }
}
```

#### POST /ideas/:id/reject
Reject idea.

```json
// Request
{ "reason": "Out of scope for current release" }
```

---

### Questions

#### GET /ideas/:ideaId/questions
List questions for an idea.

#### POST /questions/:id/answer
Answer a question.

```json
// Request
{
  "answer": "Separate inventories for each player"
}

// Response
{ "id": "uuid", "status": "answered", "answer": "..." }
```

#### POST /questions/:id/skip
Skip a question.

---

### Tickets

#### GET /projects/:projectId/tickets
List tickets (development queue).

```json
// Query params: ?status=queued,in_progress&type=feature

// Response
{
  "items": [
    {
      "id": "uuid",
      "title": "Add multiplayer",
      "type": "feature",
      "status": "in_progress",
      "priority": 2,
      "assigned_agent": "feature-dev",
      "progress": {
        "subtasks_done": 1,
        "subtasks_total": 4
      }
    }
  ]
}
```

#### POST /projects/:projectId/tickets
Create manual ticket (not from idea).

#### GET /tickets/:id
Get ticket details with subtasks and runs.

#### PATCH /tickets/:id
Update ticket.

#### POST /tickets/:id/start
Start development on ticket.

#### POST /tickets/:id/review
Move ticket to review status.

#### POST /tickets/:id/approve
Approve and merge ticket.

```json
// Request
{ "comment": "Looks good!" }
```

#### POST /tickets/:id/request-changes
Request changes on ticket.

```json
// Request
{ "feedback": "Please add error handling to..." }
```

---

### Agents

#### GET /agents
List all agents (global + project).

```json
// Query params: ?project_id=uuid&type=development

// Response
{
  "items": [
    {
      "id": "uuid",
      "name": "feature-dev",
      "description": "...",
      "type": "development",
      "model": "opus",
      "is_active": true,
      "project_id": null  // null = global
    }
  ]
}
```

#### POST /agents
Create new agent.

```json
// Request
{
  "name": "spawning-plugin",
  "description": "Handles spawning system changes",
  "type": "development",
  "model": "sonnet",
  "tools": ["Read", "Edit", "Grep", "Glob"],
  "system_prompt": "You only modify...",
  "project_id": "uuid"
}
```

#### GET /agents/:id
Get agent details.

#### PATCH /agents/:id
Update agent configuration.

#### DELETE /agents/:id
Delete agent.

#### GET /agents/:id/runs
List runs for an agent.

---

### Agent Runs

#### GET /runs/:id
Get run details with logs.

```json
// Response
{
  "id": "uuid",
  "agent_id": "uuid",
  "ticket_id": "uuid",
  "status": "running",
  "input": { ... },
  "output": null,
  "tokens_used": 1500,
  "cost_usd": 0.045,
  "started_at": "...",
  "logs": [
    { "level": "info", "message": "Starting...", "created_at": "..." }
  ]
}
```

#### POST /runs/:id/cancel
Cancel a running agent.

---

### Planning Documents

#### GET /projects/:projectId/planning
List planning documents.

#### POST /projects/:projectId/planning
Create new document.

```json
// Request
{
  "title": "Multiplayer Feature Spec",
  "type": "spec",
  "content": "# Feature Spec..."
}
```

#### GET /planning/:id
Get document content.

#### PATCH /planning/:id
Update document.

#### DELETE /planning/:id
Delete document.

#### POST /planning/:id/export
Export document.

```json
// Request
{ "format": "claude_md" }

// Response
{ "content": "# Project...", "filename": "CLAUDE.md" }
```

---

### System

#### GET /system/status
Health check and system status.

```json
// Response
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 3600,
  "queue": {
    "pending": 5,
    "running": 2
  }
}
```

#### GET /system/usage
Usage statistics.

```json
// Query params: ?period=month&project_id=uuid

// Response
{
  "period": "2026-02",
  "total_tokens": 150000,
  "total_cost_usd": 4.50,
  "by_agent": [
    { "agent": "feature-dev", "tokens": 80000, "cost": 2.40 }
  ],
  "by_day": [
    { "date": "2026-02-01", "tokens": 10000, "cost": 0.30 }
  ]
}
```

---

### WebSocket Events

#### Connection
```
ws://localhost:8000/ws?token=<jwt>
```

#### Events

```json
// Idea status changed
{
  "event": "idea.updated",
  "data": { "id": "uuid", "status": "questions" }
}

// New question
{
  "event": "question.created",
  "data": { "id": "uuid", "idea_id": "uuid", "question": "..." }
}

// Ticket progress
{
  "event": "ticket.progress",
  "data": { "id": "uuid", "subtask": "Network layer", "status": "done" }
}

// Agent run log
{
  "event": "run.log",
  "data": { "run_id": "uuid", "level": "info", "message": "..." }
}

// Build/test result
{
  "event": "build.completed",
  "data": { "ticket_id": "uuid", "success": true }
}
```

---

## Rate Limiting

| Endpoint Pattern | Limit |
|-----------------|-------|
| `/auth/*` | 10/minute |
| `POST /ideas` | 30/minute |
| `GET /*` | 100/minute |
| `POST /*/approve` | 20/minute |
| Default | 60/minute |

---

## Open Questions

| Question | Context | Decision |
|----------|---------|----------|
| Pagination style? | Offset vs cursor | TBD - offset simpler |
| Bulk operations? | Create multiple ideas | TBD - defer |
| Webhooks? | External notifications | TBD - defer to v2 |

---

## Dependencies

- **Depends on**: 01-architecture, 02-data-models
- **Depended by**: 08-web-ui

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-02-05 | Initial draft | - |
