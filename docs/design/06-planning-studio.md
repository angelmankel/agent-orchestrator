# Planning Studio

> **Status**: Draft
> **Last Updated**: 2026-02-05
> **Owner**: -
> **Depends On**: [01-architecture](01-architecture.md), [02-data-models](02-data-models.md)

---

## Overview

Planning Studio is a markdown-based product design workspace. Create roadmaps, architecture docs, feature specs, and design documents that integrate with the agent system and can bootstrap new projects.

---

## Goals

- [ ] Provide structured markdown editing for product planning
- [ ] Support common document types (roadmap, spec, architecture)
- [ ] Enable export to CLAUDE.md and project context
- [ ] Integrate with Ideas Pipeline for feature tracking
- [ ] Version control all planning documents

---

## Non-Goals

- WYSIWYG editing (markdown-first)
- Real-time collaboration (async, git-based)
- Gantt charts or complex project management

---

## Design

### Document Types

```
┌─────────────────────────────────────────────────────────────────┐
│                      PLANNING STUDIO                            │
├─────────────────┬─────────────────┬─────────────────────────────┤
│    Roadmaps     │   Specs         │    Architecture             │
├─────────────────┼─────────────────┼─────────────────────────────┤
│ • Product       │ • Feature       │ • System Design             │
│ • Release       │ • Technical     │ • Data Flow                 │
│ • Sprint        │ • API           │ • Component Map             │
│                 │ • UI/UX         │ • Integration               │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

### Document Templates

#### Product Roadmap
```markdown
# Product Roadmap: [Product Name]

## Vision
[One paragraph describing the product vision]

## Current State
- Version: [x.y.z]
- Status: [Active Development / Maintenance / Planning]

---

## Milestones

### Q1 2026 - [Theme Name]
| Feature | Priority | Status | Linked Ideas |
|---------|----------|--------|--------------|
| Feature 1 | High | Planned | #idea-123 |
| Feature 2 | Medium | In Progress | #idea-456 |

### Q2 2026 - [Theme Name]
...

---

## Backlog
Features not yet scheduled.

| Feature | Priority | Notes |
|---------|----------|-------|
| ... | ... | ... |

---

## Completed
| Feature | Shipped | Notes |
|---------|---------|-------|
| ... | Q4 2025 | ... |
```

#### Feature Specification
```markdown
# Feature Spec: [Feature Name]

> **Status**: Draft | Review | Approved | Implementing | Done
> **Owner**: [Name]
> **Target**: [Milestone]
> **Linked Ideas**: #idea-123, #idea-456

---

## Problem Statement
[What problem does this solve? Who has this problem?]

## Goals
- [ ] Goal 1
- [ ] Goal 2

## Non-Goals
- What this feature does NOT do

---

## User Stories

### Story 1: [As a... I want... So that...]
**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2

### Story 2: ...

---

## Design

### User Flow
```
[ASCII diagram or description]
```

### UI Mockups
[Link to mockups or ASCII wireframes]

### Technical Approach
[How will this be implemented?]

---

## Open Questions
| Question | Status | Decision |
|----------|--------|----------|
| ... | Open | TBD |

---

## Dependencies
- Depends on: [Other features/systems]
- Blocks: [What this unblocks]

---

## Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| ... | Medium | High | ... |
```

#### Architecture Document
```markdown
# Architecture: [System/Component Name]

> **Status**: Draft | Review | Approved
> **Last Updated**: [Date]
> **Owner**: [Name]

---

## Overview
[Brief description of the system and its purpose]

## Context
[How this fits into the larger system]

---

## Architecture Diagram

```
[ASCII diagram]
```

---

## Components

### Component 1: [Name]
- **Purpose**: [What it does]
- **Technology**: [Stack/tools]
- **Interfaces**: [APIs, events, etc.]

### Component 2: [Name]
...

---

## Data Flow

```
[Sequence diagram or flow description]
```

---

## Key Decisions

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| ... | ... | ... |

---

## Security Considerations
- [ ] Authentication
- [ ] Authorization
- [ ] Data encryption
- [ ] Input validation

---

## Performance Considerations
- Expected load: [metrics]
- Bottlenecks: [identified areas]
- Scaling strategy: [approach]

---

## Future Considerations
[What might change, extensibility points]
```

### Workspace Structure

```
project/
└── planning/
    ├── roadmaps/
    │   ├── product-roadmap.md
    │   └── release-2.0.md
    ├── specs/
    │   ├── multiplayer-feature.md
    │   └── inventory-system.md
    ├── architecture/
    │   ├── system-overview.md
    │   └── network-layer.md
    └── notes/
        └── meeting-2026-02-05.md
```

### Editor Features

#### Core Editing
- Markdown syntax highlighting
- Live preview (split pane)
- Template insertion
- Auto-save

#### Planning-Specific
- Idea linking (`#idea-123` → clickable)
- Ticket linking (`#ticket-456` → clickable)
- Status badges (renders visual status)
- Table of contents generation
- Cross-document linking

#### Diagrams
- ASCII diagram helpers
- Mermaid.js rendering (optional)
- Flowchart templates

### Integration Points

#### Ideas Pipeline
```
Planning Doc                    Ideas Inbox
     │                              │
     │ "Extract feature ideas"      │
     └──────────────────────────────>│
                                    │
                                    │ Creates ideas from
                                    │ spec requirements
                                    │
     │<─────────────────────────────┘
     │
     │ Link ideas back to spec
     │ #idea-123, #idea-456
```

#### Project Bootstrap
```
Planning Docs                   New Project
     │                              │
     │ "Initialize project"         │
     └──────────────────────────────>│
                                    │
                                    │ • Creates CLAUDE.md from architecture
                                    │ • Creates .claude/agents/ from specs
                                    │ • Imports roadmap as initial ideas
                                    │
                                    ▼
                                [Ready to develop]
```

### Export Formats

| Format | Use Case |
|--------|----------|
| CLAUDE.md | Agent context for development |
| PDF | Stakeholder sharing |
| HTML | Web publishing |
| JSON | API consumption |

#### CLAUDE.md Export
```markdown
# [Project Name]

## Overview
[Extracted from architecture overview]

## Architecture
[Extracted from architecture docs]

## Key Patterns
[Extracted from specs and architecture]

## Current Work
[Extracted from roadmap - current milestone]

## Conventions
[Extracted from specs - technical approach sections]
```

---

## UI Design

### Studio Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ Planning Studio                              [+ New] [Export ▼] │
├─────────────────────────────────────────────────────────────────┤
│ ┌───────────┐ ┌─────────────────────────────────────────────────┤
│ │ Documents │ │ # Feature Spec: Multiplayer                     │
│ │           │ │                                                 │
│ │ ▼ Roadmaps│ │ > Status: Draft                                 │
│ │   product │ │ > Owner: @donny                                 │
│ │   release │ │                                                 │
│ │           │ │ ## Problem Statement                            │
│ │ ▼ Specs   │ │                                                 │
│ │  >multipl │ │ Players want to enjoy the game with friends...  │
│ │   invent  │ │                                                 │
│ │           │ │ ## Goals                                        │
│ │ ▼ Arch    │ │ - [ ] Support 2-4 players                       │
│ │   system  │ │ - [ ] Low-latency sync                          │
│ │   network │ │                                                 │
│ │           │ │ ## User Stories                                 │
│ │ + New Doc │ │ ...                                             │
│ └───────────┘ └─────────────────────────────────────────────────┤
│               │ Preview │ Edit │                     [Save] │
└─────────────────────────────────────────────────────────────────┘
```

### Document Browser

```
┌─────────────────────────────────────────────────────────────────┐
│ All Documents                     [Search...] [Filter ▼] [+ New]│
├─────────────────────────────────────────────────────────────────┤
│ Name                    Type        Status      Updated         │
├─────────────────────────────────────────────────────────────────┤
│ 📋 Product Roadmap      Roadmap     Active      2h ago          │
│ 📄 Multiplayer Feature  Spec        Draft       30m ago         │
│ 📄 Inventory System     Spec        Approved    2d ago          │
│ 🏗️ System Overview      Arch        Approved    1w ago          │
│ 🏗️ Network Layer        Arch        Draft       1d ago          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Models

```sql
CREATE TABLE planning_docs (
    id              TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL REFERENCES projects(id),
    title           TEXT NOT NULL,
    type            TEXT NOT NULL,  -- 'roadmap', 'spec', 'architecture', 'note'
    path            TEXT NOT NULL,  -- relative file path
    status          TEXT DEFAULT 'draft',
    content_hash    TEXT,           -- for change detection
    metadata        TEXT,           -- JSON blob
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_planning_docs_project ON planning_docs(project_id);
CREATE INDEX idx_planning_docs_type ON planning_docs(type);
```

---

## Open Questions

| Question | Context | Decision |
|----------|---------|----------|
| Version history? | Track doc changes over time | TBD - rely on git |
| Collaborative editing? | Multiple users same doc | TBD - defer, use git |
| AI assistance in writing? | Help draft specs | TBD - could add planning agents |

---

## Dependencies

- **Depends on**: 01-architecture, 02-data-models
- **Depended by**: 08-web-ui, 09-configuration

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-02-05 | Initial draft | - |
