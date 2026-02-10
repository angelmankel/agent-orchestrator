# Agent System

> **Status**: Draft
> **Last Updated**: 2026-02-05
> **Owner**: -
> **Depends On**: [01-architecture](01-architecture.md), [02-data-models](02-data-models.md)

---

## Overview

Defines how agents are created, configured, orchestrated, and executed. Covers agent types, lifecycle, communication patterns, and integration with the Claude API.

---

## Goals

- [ ] Define agent types and their responsibilities
- [ ] Establish agent configuration schema
- [ ] Design orchestration patterns (sequential, parallel, conditional)
- [ ] Enable agent memory and learning across runs
- [ ] Support both global and project-specific agents

---

## Non-Goals

- Agents modifying their own definitions (human-controlled)
- Cross-project agent communication
- Real-time agent collaboration (async handoffs instead)

---

## Design

### Agent Types

```
┌─────────────────────────────────────────────────────────────────┐
│                        Agent Types                              │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│   Refinement    │   Development   │     Support     │  Planning │
├─────────────────┼─────────────────┼─────────────────┼───────────┤
│ • Clarifier     │ • Feature Dev   │ • Builder       │ • Analyst │
│ • Researcher    │ • Bugfix Dev    │ • Tester        │ • Architect│
│ • Estimator     │ • Refactor Dev  │ • Reviewer      │ • Writer  │
│ • Prioritizer   │ • Docs Dev      │ • Deployer      │           │
└─────────────────┴─────────────────┴─────────────────┴───────────┘
```

#### Refinement Agents
Process raw ideas into structured, actionable tickets.

| Agent | Purpose | Tools |
|-------|---------|-------|
| **Clarifier** | Ask questions to understand intent | Read, Grep, Glob |
| **Researcher** | Find related code and prior art | Read, Grep, Glob, WebSearch |
| **Estimator** | Break down into subtasks and estimate complexity | Read, Grep, Glob |
| **Prioritizer** | Suggest priority based on impact/effort | Read, Grep, Glob |

#### Development Agents
Implement approved tickets.

| Agent | Purpose | Tools |
|-------|---------|-------|
| **Feature Dev** | Implement new functionality | Read, Edit, Write, Grep, Glob |
| **Bugfix Dev** | Fix reported issues | Read, Edit, Write, Grep, Glob, Bash |
| **Refactor Dev** | Improve code structure | Read, Edit, Write, Grep, Glob |
| **Docs Dev** | Write documentation | Read, Edit, Write, Grep, Glob |

#### Support Agents
Assist development agents with specific tasks.

| Agent | Purpose | Tools |
|-------|---------|-------|
| **Builder** | Compile and build projects | Bash, Read |
| **Tester** | Run tests and report results | Bash, Read, Grep |
| **Reviewer** | Review code changes for quality | Read, Grep, Glob |
| **Deployer** | Deploy to environments | Bash, Read |

#### Planning Agents
Help with product design and planning.

| Agent | Purpose | Tools |
|-------|---------|-------|
| **Analyst** | Analyze requirements and constraints | Read, Grep, Glob, WebSearch |
| **Architect** | Design system architecture | Read, Grep, Glob, Write |
| **Writer** | Write specs and documentation | Read, Write |

### Agent Configuration Schema

```yaml
# Agent definition schema
name: string              # unique identifier (lowercase, hyphens)
description: string       # when/why to use this agent
type: enum                # refinement | development | support | planning

# Execution settings
model: enum               # haiku | sonnet | opus
tools: array[string]      # allowed tools
disallowed_tools: array   # explicitly blocked tools
max_turns: integer        # max API round-trips
timeout_seconds: integer  # max execution time

# Prompt configuration
system_prompt: string     # base instructions
context_files: array      # files to always include
memory_scope: enum        # none | session | project | global

# Restrictions
allowed_paths: array      # glob patterns for file access
blocked_paths: array      # glob patterns to block
require_approval: array   # actions needing human approval

# Metadata
project_id: string|null   # null = global agent
is_active: boolean
tags: array[string]
```

### Example Agent Definitions

#### Clarifier Agent
```yaml
name: clarifier
description: Asks clarifying questions to understand idea intent and scope
type: refinement
model: sonnet
tools:
  - Read
  - Grep
  - Glob
system_prompt: |
  You are a product analyst. Your job is to understand user ideas deeply.

  For each idea:
  1. Identify ambiguous requirements
  2. Ask 2-5 specific, targeted questions
  3. Consider edge cases and constraints
  4. Think about existing system impact

  Format questions clearly. Explain why each question matters.
  Do NOT assume answers. Do NOT propose solutions yet.
memory_scope: project
max_turns: 5
```

#### Feature Developer Agent
```yaml
name: feature-dev
description: Implements new features based on approved tickets
type: development
model: opus
tools:
  - Read
  - Edit
  - Write
  - Grep
  - Glob
disallowed_tools:
  - Bash  # Support agents handle builds
system_prompt: |
  You are a senior developer implementing new features.

  Guidelines:
  1. Read the ticket spec thoroughly before coding
  2. Follow existing code patterns and conventions
  3. Write clean, maintainable code
  4. Add comments only where logic is non-obvious
  5. Do NOT run builds or tests (support agents do that)

  When done, summarize what you implemented and what needs testing.
memory_scope: project
allowed_paths:
  - "src/**/*"
  - "lib/**/*"
blocked_paths:
  - "**/.env*"
  - "**/secrets/**"
require_approval:
  - Write(new files)
max_turns: 20
```

#### Builder Agent
```yaml
name: builder
description: Compiles projects and reports build status
type: support
model: haiku
tools:
  - Bash
  - Read
system_prompt: |
  You are a build specialist. Your only job is to run builds.

  Process:
  1. Read the project's build configuration
  2. Run the appropriate build command
  3. Parse output for errors and warnings
  4. Return structured results: success/failure, errors, warnings

  Do NOT fix code. Report issues back for dev agents to handle.
memory_scope: session
max_turns: 3
timeout_seconds: 300
```

### Agent Lifecycle

```
┌─────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐
│ Created │───>│ Queued   │───>│ Running │───>│ Complete │
└─────────┘    └──────────┘    └────┬────┘    └──────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
              ┌──────────┐  ┌───────────┐  ┌──────────┐
              │ Waiting  │  │  Failed   │  │ Cancelled│
              │ Approval │  │           │  │          │
              └──────────┘  └───────────┘  └──────────┘
```

### Orchestration Patterns

#### Sequential Chain
```
Clarifier → Researcher → Estimator → [Human Approval] → Feature Dev → Builder → Tester
```

#### Parallel Execution
```
                    ┌─→ Researcher ─┐
Idea Submitted ────>│               │────> Merge Results → Human Review
                    └─→ Estimator ──┘
```

#### Conditional Routing
```
Ticket Type?
├─ feature  → Feature Dev
├─ bugfix   → Bugfix Dev
├─ refactor → Refactor Dev
└─ docs     → Docs Dev
```

#### Support Loop
```
Feature Dev ←──────────────────────┐
     │                             │
     ▼                             │
Builder ──→ Success? ──No──→ Report Errors
     │
    Yes
     ▼
Tester ──→ Pass? ──No──→ Report Failures
     │
    Yes
     ▼
  Done
```

### Agent Memory

#### Scopes

| Scope | Persists | Location | Use Case |
|-------|----------|----------|----------|
| none | Never | - | Stateless operations |
| session | Current run | Memory | Multi-turn context |
| project | Across runs | `.agent-memory/{agent}/` | Learned patterns |
| global | Everywhere | `~/.agent-memory/{agent}/` | Cross-project knowledge |

#### Memory Structure
```
.agent-memory/
└── feature-dev/
    ├── MEMORY.md           # Key learnings
    ├── patterns.md         # Code patterns discovered
    └── gotchas.md          # Project-specific issues
```

### Agent Communication

Agents don't talk directly to each other. They communicate through:

1. **Tickets/Subtasks**: Structured work items
2. **Run Results**: Output from previous agent
3. **Shared Files**: Project files and memory
4. **Queue Events**: Status updates

```
Agent A completes → Result stored in DB → Queue notifies → Agent B reads result → Continues work
```

---

## Open Questions

| Question | Context | Decision |
|----------|---------|----------|
| Agent self-improvement? | Can agents update their prompts based on feedback? | TBD - risky, defer |
| Cross-agent memory? | Should agents share learned knowledge? | TBD - start isolated |
| Dynamic tool grants? | Can agents request additional tools mid-run? | TBD - security concern |

---

## Dependencies

- **Depends on**: 01-architecture, 02-data-models
- **Depended by**: 04-ideas-pipeline, 05-development-pipeline, 09-configuration

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-02-05 | Initial draft | - |
