# Agent Orchestrator

A generic, configurable multi-agent development platform that processes ideas through refinement, approval, and implementation pipelines.

## Vision

Access a web UI from any device to:
- Submit ideas that agents refine and clarify
- Approve refined tickets for development
- Monitor agent-driven development with human checkpoints
- Design and plan projects using structured markdown tools

## Design Documents

All design documents follow a common format and are located in `docs/design/`:

| Document | Description | Status |
|----------|-------------|--------|
| [01-architecture](docs/design/01-architecture.md) | System architecture and component overview | Draft |
| [02-data-models](docs/design/02-data-models.md) | SQLite schema and data structures | Draft |
| [03-agent-system](docs/design/03-agent-system.md) | Agent definitions, configuration, orchestration | Draft |
| [04-ideas-pipeline](docs/design/04-ideas-pipeline.md) | Idea submission to approval flow | Draft |
| [05-development-pipeline](docs/design/05-development-pipeline.md) | Approved ticket to implemented code | Draft |
| [06-planning-studio](docs/design/06-planning-studio.md) | Markdown-based product design tools | Draft |
| [07-api-design](docs/design/07-api-design.md) | REST API endpoints and contracts | Draft |
| [08-web-ui](docs/design/08-web-ui.md) | Frontend pages and components | Draft |
| [09-configuration](docs/design/09-configuration.md) | Project and agent configuration system | Draft |
| [10-auth-access](docs/design/10-auth-access.md) | Authentication and permissions | Draft |
| [11-cost-management](docs/design/11-cost-management.md) | Token tracking, limits, budgets | Draft |
| [12-project-templates](docs/design/12-project-templates.md) | Reusable project type configurations | Draft |

## Tech Stack (Proposed)

- **Database**: SQLite (fast, portable, single-file)
- **Backend**: Python (FastAPI) or TypeScript (Node/Hono)
- **Frontend**: React or Svelte (lightweight, fast)
- **Agent Runtime**: Claude API via Agent SDK
- **Queue**: SQLite-backed job queue (or Redis for scale)

## Project Status

This project is being designed using its own planning methodology.

---

*This project serves as both a product and a template for AI-assisted development workflows.*
