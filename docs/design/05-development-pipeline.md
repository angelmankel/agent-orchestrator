# Development Pipeline

> **Status**: Draft
> **Last Updated**: 2026-02-05
> **Owner**: -
> **Depends On**: [02-data-models](02-data-models.md), [03-agent-system](03-agent-system.md), [04-ideas-pipeline](04-ideas-pipeline.md)

---

## Overview

The Development Pipeline takes approved tickets and orchestrates agents to implement, build, test, and review code changes. Emphasizes granular agent focus with support agents handling builds and tests.

---

## Goals

- [ ] Orchestrate development agents for code implementation
- [ ] Coordinate support agents (build, test, review)
- [ ] Maintain human checkpoints before merge
- [ ] Track progress through subtasks
- [ ] Handle failures gracefully with clear reporting

---

## Non-Goals

- Fully autonomous deployment (human approval required)
- Multi-branch parallel development (one ticket at a time per agent)
- Direct code execution in production

---

## Design

### Pipeline Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         DEVELOPMENT PIPELINE                             │
└──────────────────────────────────────────────────────────────────────────┘

 ┌─────────┐    ┌───────────┐    ┌─────────┐    ┌────────┐    ┌──────────┐
 │ Queued  │───>│  Develop  │───>│  Build  │───>│  Test  │───>│  Review  │
 │         │    │           │    │         │    │        │    │          │
 └─────────┘    └─────┬─────┘    └────┬────┘    └───┬────┘    └────┬─────┘
                      │               │             │              │
                      │◄──── Fail ────┤             │              │
                      │◄────────── Fail ────────────┤              │
                      │                                            ▼
                      │                                     ┌────────────┐
                      │                                     │   Human    │
                      │                                     │   Review   │
                      │                                     └─────┬──────┘
                      │                                           │
                      │◄─────────── Request Changes ──────────────┤
                      │                                           │
                      │                                           ▼
                      │                                     ┌──────────┐
                      │                                     │  Merge   │
                      │                                     └────┬─────┘
                      │                                          │
                      └──────────────────────────────────────────>│ Done
```

### States

| State | Description | Next States |
|-------|-------------|-------------|
| `queued` | Approved ticket waiting for agent | in_progress |
| `in_progress` | Agent actively developing | review, blocked |
| `review` | Code complete, awaiting human review | done, in_progress |
| `blocked` | Waiting for dependency or human input | in_progress |
| `done` | Merged and complete | - |
| `cancelled` | Ticket abandoned | - |

### Agent Orchestration

#### Development Cycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT CYCLE                            │
└─────────────────────────────────────────────────────────────────┘

                         ┌─────────────┐
                         │   Ticket    │
                         │   Assigned  │
                         └──────┬──────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │    Route by Type      │
                    └───────────┬───────────┘
                                │
         ┌──────────┬───────────┼───────────┬──────────┐
         ▼          ▼           ▼           ▼          ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
    │ Feature │ │ Bugfix  │ │Refactor │ │  Docs   │ │  Chore  │
    │   Dev   │ │   Dev   │ │   Dev   │ │   Dev   │ │   Dev   │
    └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
         │          │           │           │          │
         └──────────┴───────────┼───────────┴──────────┘
                                │
                                ▼
                         ┌─────────────┐
                         │   Builder   │◄────────────┐
                         │   Agent     │             │
                         └──────┬──────┘             │
                                │                    │
                         Pass? ─┼─ No ───> Report ───┘
                                │           Errors
                               Yes
                                │
                                ▼
                         ┌─────────────┐
                         │   Tester    │◄────────────┐
                         │   Agent     │             │
                         └──────┬──────┘             │
                                │                    │
                         Pass? ─┼─ No ───> Report ───┘
                                │           Failures
                               Yes
                                │
                                ▼
                         ┌─────────────┐
                         │  Reviewer   │
                         │   Agent     │
                         └──────┬──────┘
                                │
                                ▼
                         ┌─────────────┐
                         │   Human     │
                         │   Review    │
                         └─────────────┘
```

#### Agent Responsibilities

| Agent | Focus | Does NOT Do |
|-------|-------|-------------|
| **Feature Dev** | Write new code | Run builds, run tests |
| **Bugfix Dev** | Fix specific issue | Add features, refactor |
| **Refactor Dev** | Improve structure | Change behavior |
| **Builder** | Compile, report errors | Fix code |
| **Tester** | Run tests, report failures | Fix tests |
| **Reviewer** | Check quality, suggest improvements | Make changes |

### Subtask Execution

Tickets break down into subtasks executed sequentially:

```
Ticket: Add multiplayer support
├── Subtask 1: Network layer setup [done]
│   └── Agent: feature-dev
├── Subtask 2: Player sync system [in_progress]
│   └── Agent: feature-dev
├── Subtask 3: Lobby UI [pending]
│   └── Agent: feature-dev
└── Subtask 4: Documentation [pending]
    └── Agent: docs-dev
```

#### Subtask States

| State | Description |
|-------|-------------|
| `pending` | Not started |
| `in_progress` | Agent working |
| `done` | Completed successfully |
| `skipped` | Intentionally skipped |
| `blocked` | Waiting for something |

### Build Integration

#### Build Trigger Points
1. After each subtask completion
2. Before test execution
3. On human request

#### Build Agent Flow
```python
# Pseudocode
def run_build(ticket, project):
    # 1. Determine build command
    build_cmd = project.config.build_command

    # 2. Execute build
    result = bash.run(build_cmd, timeout=300)

    # 3. Parse output
    errors = parse_errors(result.stdout)
    warnings = parse_warnings(result.stdout)

    # 4. Return structured result
    return {
        "success": result.exit_code == 0,
        "errors": errors,
        "warnings": warnings,
        "duration_seconds": result.duration
    }
```

#### Build Failure Handling
```
Build Failed
    │
    ├─> Parse error messages
    │
    ├─> Identify affected files
    │
    ├─> Create error report
    │
    └─> Return to Dev Agent with:
        • Error messages
        • File locations
        • Suggested fixes (if determinable)
```

### Test Integration

#### Test Agent Flow
```python
# Pseudocode
def run_tests(ticket, project, scope="affected"):
    # 1. Determine test scope
    if scope == "affected":
        test_files = find_affected_tests(ticket.changed_files)
    else:
        test_files = project.config.test_pattern

    # 2. Execute tests
    result = bash.run(f"{project.config.test_command} {test_files}")

    # 3. Parse results
    passed, failed, skipped = parse_test_output(result.stdout)

    # 4. Return structured result
    return {
        "success": len(failed) == 0,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "coverage": parse_coverage(result.stdout)
    }
```

#### Test Failure Handling
```
Tests Failed
    │
    ├─> Identify failing tests
    │
    ├─> Extract failure messages
    │
    ├─> Correlate with changed code
    │
    └─> Return to Dev Agent with:
        • Failed test names
        • Assertion messages
        • Stack traces
        • Related changed files
```

### Code Review

#### Automated Review (Reviewer Agent)
```
Review Checklist:
□ Code follows project conventions
□ No obvious security issues
□ No hardcoded secrets
□ Error handling present
□ Changes match ticket scope
□ No unnecessary complexity
```

#### Human Review Interface
```
┌─────────────────────────────────────────────────────────────┐
│ CODE REVIEW: Add multiplayer support                        │
├─────────────────────────────────────────────────────────────┤
│ Changed Files:                                              │
│ + src/network/connection.cpp (new)                          │
│ + src/network/sync.cpp (new)                                │
│ M src/player/player.cpp (+45, -12)                          │
│ M src/ui/lobby.cpp (+120, -0)                               │
├─────────────────────────────────────────────────────────────┤
│ Automated Review:                                           │
│ ✅ Follows conventions                                      │
│ ✅ No security issues detected                              │
│ ✅ Error handling present                                   │
│ ⚠️ Consider adding timeout to connection.cpp:45             │
├─────────────────────────────────────────────────────────────┤
│ Build: ✅ Success (2m 34s)                                  │
│ Tests: ✅ 47 passed, 0 failed                               │
├─────────────────────────────────────────────────────────────┤
│ [View Diff] [View Full Files]                               │
│                                                             │
│ Comments:                                                   │
│ [____________________________________]                      │
│                                                             │
│ [Approve & Merge] [Request Changes] [Reject]                │
└─────────────────────────────────────────────────────────────┘
```

### Merge Process

1. Human approves review
2. System creates commit with attribution
3. Commit pushed to branch
4. Optional: PR created for team review
5. Ticket marked as `done`

#### Commit Format
```
feat: Add multiplayer support (#ticket-123)

- Implemented network layer for player connections
- Added player state synchronization
- Created lobby UI for game joining

Subtasks completed:
- Network layer setup
- Player sync system
- Lobby UI
- Documentation

Developed-By: feature-dev (Agent)
Reviewed-By: reviewer (Agent)
Approved-By: user@example.com
```

---

## Error Recovery

### Retry Logic
```
Max Attempts: 3
Backoff: exponential (1s, 5s, 30s)

On failure:
1. Log error details
2. If retriable: queue retry
3. If max attempts: mark blocked, notify human
```

### Blocked Tickets
```
Blocked reasons:
- Build failures after 3 attempts
- Test failures after 3 attempts
- Missing dependency
- Agent timeout
- Human intervention required

Resolution:
1. Human reviews block reason
2. Human provides guidance or fixes
3. Ticket returns to queue
```

---

## Open Questions

| Question | Context | Decision |
|----------|---------|----------|
| Parallel subtasks? | Some subtasks could run concurrently | TBD - start sequential |
| Auto-merge low-risk? | Small changes might not need review | TBD - always review first |
| Rollback support? | Undo merged changes | TBD - rely on git for now |

---

## Dependencies

- **Depends on**: 02-data-models, 03-agent-system, 04-ideas-pipeline
- **Depended by**: 08-web-ui, 11-cost-management

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-02-05 | Initial draft | - |
