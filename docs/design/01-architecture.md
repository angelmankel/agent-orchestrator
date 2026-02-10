# System Architecture

> **Status**: Draft
> **Last Updated**: 2026-02-05
> **Owner**: -
> **Depends On**: None (foundational)

---

## Overview

High-level system architecture for the Agent Orchestrator platform. Defines the core components, how they interact, and the technology choices that enable a portable, fast, and extensible system.

---

## Goals

- [ ] Define core system components and their responsibilities
- [ ] Establish communication patterns between components
- [ ] Choose technology stack that prioritizes simplicity and portability
- [ ] Enable both local and hosted deployment modes

---

## Non-Goals

- Microservices architecture (keep it monolithic for simplicity)
- Multi-tenant SaaS (single-user/team focus initially)
- Real-time collaboration (async-first)

---

## Design

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                            Web UI                                   │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │   Ideas     │  │   Development   │  │    Planning Studio      │  │
│  │   Inbox     │  │      Queue      │  │                         │  │
│  └──────┬──────┘  └────────┬────────┘  └────────────┬────────────┘  │
└─────────┼──────────────────┼───────────────────────┼────────────────┘
          │                  │                       │
          ▼                  ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           API Layer                                 │
│                    (REST API - FastAPI/Hono)                        │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Job Queue   │    │  SQLite DB    │    │ File Storage  │
│  (async work) │    │ (all state)   │    │ (projects)    │
└───────┬───────┘    └───────────────┘    └───────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Agent Runtime                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │
│  │ Refinement  │  │ Development │  │   Support   │  │  Planning  │  │
│  │   Agents    │  │   Agents    │  │   Agents    │  │   Agents   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌───────────────┐
                    │  Claude API   │
                    └───────────────┘
```

### Core Components

#### 1. Web UI
- Single-page application (SPA)
- Three main views: Ideas, Development, Planning
- Responsive for mobile access
- Real-time updates via polling or WebSocket

#### 2. API Layer
- RESTful endpoints for all operations
- Handles authentication and authorization
- Validates requests before processing
- Returns structured JSON responses

#### 3. SQLite Database
- Single file, portable, fast
- Stores all persistent state:
  - Projects and configuration
  - Ideas and tickets
  - Agent definitions and runs
  - User data and sessions

#### 4. Job Queue
- SQLite-backed queue for async agent work
- Processes jobs in order with priority support
- Handles retries and failure states
- Enables "fire and forget" from API

#### 5. Agent Runtime
- Orchestrates Claude API calls
- Manages agent context and memory
- Enforces tool restrictions per agent
- Reports progress and results back to queue

#### 6. File Storage
- Project source code directories
- Agent memory files
- Generated artifacts and logs

### Communication Flow

```
User Action → API → Database + Queue → Agent Runtime → Claude API
                         ↓
                    Status Updates → WebSocket/Poll → UI
```

### Deployment Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| Local | Run on developer machine | Personal use, development |
| Self-hosted | Run on private server | Team use, privacy |
| Cloud | Hosted service | Convenience, accessibility |

---

## Technology Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Database | SQLite | Portable, fast, no setup, single file backup |
| Backend | Python + FastAPI | Rapid development, good Claude SDK support |
| Frontend | Svelte | Lightweight, fast, simple state management |
| Queue | SQLite-backed | No external dependencies, portable |
| Agent SDK | Claude Agent SDK | Official, maintained, full-featured |

---

## Open Questions

| Question | Context | Decision |
|----------|---------|----------|
| WebSocket vs Polling? | Real-time updates to UI | TBD - polling simpler, WS more responsive |
| Single binary distribution? | Ease of installation | TBD - consider PyInstaller or Docker |
| Plugin system? | Extensibility for custom agents | TBD - defer to later phase |

---

## Dependencies

- **Depends on**: None
- **Depended by**: All other design documents

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-02-05 | Initial draft | - |
