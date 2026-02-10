# Agent Orchestrator

Multi-agent development platform with web UI for idea refinement, development orchestration, and project planning.

## Project Structure

```
agent-orchestrator/
├── docs/
│   ├── IMPLEMENTATION.md    # Build roadmap (start here)
│   └── design/              # Full design specs (01-12)
├── backend/                 # Python + FastAPI (to be created)
├── frontend/                # Svelte web UI (to be created)
└── templates/               # Project templates (to be created)
```

## Tech Stack

- **Database**: SQLite (single file, portable)
- **Backend**: Python + FastAPI
- **Frontend**: Svelte
- **Agent Runtime**: Claude API (anthropic package)

## Key Design Docs

| Doc | Purpose |
|-----|---------|
| `02-data-models.md` | SQLite schema |
| `03-agent-system.md` | Agent types and orchestration |
| `04-ideas-pipeline.md` | Idea → approval flow |
| `05-development-pipeline.md` | Ticket → merge flow |
| `07-api-design.md` | REST API endpoints |

## Current Phase

**Phase 1: Foundation** - Database, API skeleton, basic agent runtime.

## Commands

```bash
# Backend (once created)
cd backend && uvicorn main:app --reload

# Frontend (once created)
cd frontend && npm run dev
```
