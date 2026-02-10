# Implementation Roadmap

> Quick reference for building Agent Orchestrator. See `/docs/design/` for full specs.

---

## Phase 1: Foundation

### 1.1 Database & Models
- [x] SQLite setup with schema from `02-data-models.md`
- [x] Core tables: projects, ideas, tickets, agents, job_queue
- [x] Basic CRUD operations

### 1.2 API Skeleton
- [x] FastAPI project structure
- [x] Health check endpoint
- [x] Error handling middleware
- [x] CORS configuration

### 1.3 Agent Runtime
- [x] Claude API integration
- [x] Basic agent execution (single agent, single run)
- [x] Token tracking per run

**Milestone**: Can create a project, define an agent, and run it manually.

---

## Phase 2: Ideas Pipeline

### 2.1 Idea Submission
- [x] POST /ideas endpoint
- [x] Idea storage and retrieval

### 2.2 Refinement Agents
- [x] Clarifier agent (generates questions)
- [x] Job queue for async processing
- [x] Question storage

### 2.3 Q&A Flow
- [x] GET /questions endpoint
- [x] POST /questions/:id/answer
- [x] Re-trigger refinement after answers

### 2.4 Approval
- [x] Approval endpoint
- [x] Idea → Ticket conversion

**Milestone**: Submit idea → get questions → answer → approve → ticket created.

---

## Phase 3: Development Pipeline

### 3.1 Ticket Queue
- [x] Ticket listing and filtering
- [x] Priority ordering
- [x] Status transitions

### 3.2 Development Agents
- [x] Route tickets by type to agents
- [x] Subtask tracking
- [x] Agent run history

### 3.3 Support Agents
- [x] Builder agent (runs build command)
- [x] Tester agent (runs tests)
- [x] Reviewer agent (code review)

### 3.4 Human Review
- [x] Review endpoint with diff summary
- [x] Approve/reject/request changes

**Milestone**: Ticket flows through dev → build → test → review → done.

---

## Phase 4: Web UI

### 4.1 Setup
- [x] Svelte/React project
- [x] API client
- [ ] Auth flow (if enabled)

### 4.2 Core Pages
- [x] Dashboard
- [x] Ideas Inbox + Q&A interface
- [x] Development Queue
- [x] Ticket Detail with live logs

### 4.3 Agent Management
- [x] Agent list/create/edit
- [ ] Run history view

**Milestone**: Full workflow accessible via web UI.

---

## Phase 5: Planning Studio

### 5.1 Document Management
- [ ] Planning docs CRUD
- [ ] Markdown editor with preview

### 5.2 Templates
- [ ] Roadmap, spec, architecture templates
- [ ] Idea linking (#idea-123)

### 5.3 Export
- [ ] CLAUDE.md generation
- [ ] Project bootstrap from planning docs

**Milestone**: Design docs that feed into project setup.

---

## Phase 6: Polish

### 6.1 Configuration
- [ ] Project templates (UE5, web, etc.)
- [ ] Config file loading and merging

### 6.2 Cost Management
- [ ] Usage dashboard
- [ ] Budgets and limits
- [ ] Alerts

### 6.3 Auth (if hosted)
- [ ] User management
- [ ] Role-based access
- [ ] Audit logging

---

## Tech Stack

| Component | Choice |
|-----------|--------|
| Database | SQLite |
| Backend | Python + FastAPI |
| Frontend | Svelte (or React) |
| Agent SDK | Claude API (anthropic package) |
| Queue | SQLite-backed (simple) |

---

## Quick Start Commands

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## Key Files to Create First

```
agent-orchestrator/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── database.py          # SQLite connection
│   ├── models/              # Pydantic models
│   ├── routes/              # API endpoints
│   ├── agents/              # Agent runtime
│   └── queue/               # Job queue
├── frontend/
│   ├── src/
│   │   ├── routes/          # Pages
│   │   ├── lib/             # Components
│   │   └── api/             # API client
│   └── package.json
└── templates/               # Project templates
```

---

## Current Status

**Phases 1-4 complete** (2026-02-10):
- Backend: FastAPI + SQLite with full schema
- Ideas Pipeline: Refinement, Q&A, approval flow
- Dev Pipeline: Developer, builder, tester, reviewer agents
- Web UI: Svelte dashboard, ideas inbox, dev queue, agents page

## Next Step

Continue with Phase 5: Planning Studio (document management, templates, export).
