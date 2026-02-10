# Ideas Pipeline

> **Status**: Draft
> **Last Updated**: 2026-02-05
> **Owner**: -
> **Depends On**: [02-data-models](02-data-models.md), [03-agent-system](03-agent-system.md)

---

## Overview

The Ideas Pipeline transforms raw ideas into approved, well-specified tickets ready for development. It handles idea submission, agent-driven refinement, human Q&A, and approval workflows.

---

## Goals

- [ ] Enable idea submission from any device (web, API, CLI)
- [ ] Automate idea refinement through specialized agents
- [ ] Support async human-in-the-loop Q&A
- [ ] Produce high-quality ticket specifications
- [ ] Track idea lifecycle and history

---

## Non-Goals

- Real-time chat with agents (async Q&A instead)
- Automatic approval (always requires human)
- Idea merging or deduplication (manual for now)

---

## Design

### Pipeline Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            IDEAS PIPELINE                                │
└──────────────────────────────────────────────────────────────────────────┘

   ┌─────────┐     ┌───────────┐     ┌───────────┐     ┌─────────────────┐
   │ Submit  │────>│  Refine   │────>│ Questions │────>│ Human Approval  │
   │  Idea   │     │  (Agents) │     │   (Q&A)   │     │                 │
   └─────────┘     └───────────┘     └───────────┘     └────────┬────────┘
                                                                │
                         ┌──────────────────────────────────────┼─────┐
                         │                                      │     │
                         ▼                                      ▼     ▼
                   ┌───────────┐                          ┌─────────┐ ┌────────┐
                   │  Revise   │                          │ Convert │ │ Reject │
                   │           │                          │ to      │ │        │
                   └─────┬─────┘                          │ Ticket  │ └────────┘
                         │                                └─────────┘
                         └──────────> Back to Refine
```

### States

| State | Description | Next States |
|-------|-------------|-------------|
| `pending` | Just submitted, awaiting processing | refining |
| `refining` | Agents analyzing and researching | questions, approved |
| `questions` | Waiting for human answers | refining, approved |
| `approved` | Human approved, ready for conversion | converted |
| `rejected` | Human rejected | - |
| `converted` | Turned into a ticket | - |

### Submission

#### Input Format
```json
{
  "title": "Add multiplayer support",
  "description": "Players should be able to join each other's games and play together. Support 2-4 players in co-op mode.",
  "source": "web",
  "priority": 0,
  "metadata": {
    "submitted_by": "user@example.com",
    "tags": ["multiplayer", "feature"]
  }
}
```

#### Submission Sources

| Source | Method | Use Case |
|--------|--------|----------|
| Web UI | Form submission | Primary interface |
| API | POST /ideas | Integrations |
| CLI | `orch idea submit` | Developer workflow |
| Email | Webhook parser | Mobile convenience |

### Refinement Process

#### Agent Sequence

```
1. Clarifier Agent
   ├─ Reads idea
   ├─ Analyzes for ambiguity
   └─ Generates clarifying questions

2. Researcher Agent (parallel)
   ├─ Searches codebase for related code
   ├─ Finds prior similar implementations
   └─ Notes potential conflicts

3. Estimator Agent (after questions answered)
   ├─ Breaks into subtasks
   ├─ Assesses complexity
   └─ Suggests priority
```

#### Refinement Output
```json
{
  "idea_id": "uuid",
  "analysis": {
    "clarity_score": 0.7,
    "related_files": ["src/network/", "src/player/"],
    "similar_features": ["chat-system", "leaderboards"],
    "potential_conflicts": ["save-system"]
  },
  "questions": [
    {
      "id": "q1",
      "question": "Should players share inventory or have separate inventories?",
      "context": "This affects the save system architecture significantly.",
      "options": ["Shared", "Separate", "Configurable"]
    }
  ],
  "subtasks": [
    {"title": "Network layer setup", "complexity": "high"},
    {"title": "Player sync system", "complexity": "high"},
    {"title": "Lobby UI", "complexity": "medium"}
  ],
  "suggested_priority": 2,
  "estimated_complexity": "high"
}
```

### Question & Answer

#### Question Structure
```json
{
  "id": "uuid",
  "idea_id": "uuid",
  "agent_id": "clarifier",
  "question": "Should players share inventory or have separate inventories?",
  "context": "This affects the save system architecture significantly.",
  "options": ["Shared", "Separate", "Configurable"],
  "status": "pending",
  "answer": null
}
```

#### Answer Flow
1. Questions appear in Ideas Inbox UI
2. Human reviews question and context
3. Human provides answer (select option or free text)
4. Answer saved, idea returns to `refining` state
5. Agents continue with new context

### Approval

#### Approval View
```
┌─────────────────────────────────────────────────────────────┐
│ IDEA: Add multiplayer support                               │
├─────────────────────────────────────────────────────────────┤
│ Original Description:                                       │
│ Players should be able to join each other's games...        │
├─────────────────────────────────────────────────────────────┤
│ Research Findings:                                          │
│ • Related: src/network/, src/player/                        │
│ • Similar: chat-system, leaderboards                        │
│ • Conflicts: May affect save-system                         │
├─────────────────────────────────────────────────────────────┤
│ Answered Questions:                                         │
│ Q: Shared or separate inventory?                            │
│ A: Separate inventories for each player                     │
├─────────────────────────────────────────────────────────────┤
│ Proposed Subtasks:                                          │
│ □ Network layer setup (high)                                │
│ □ Player sync system (high)                                 │
│ □ Lobby UI (medium)                                         │
├─────────────────────────────────────────────────────────────┤
│ Suggested Priority: High                                    │
│ Estimated Complexity: High                                  │
├─────────────────────────────────────────────────────────────┤
│ [Approve] [Request Changes] [Reject]                        │
└─────────────────────────────────────────────────────────────┘
```

#### Approval Actions

| Action | Result |
|--------|--------|
| **Approve** | Creates ticket with subtasks, moves to dev queue |
| **Request Changes** | Returns to `refining` with feedback |
| **Reject** | Marks as rejected with reason |

### Ticket Conversion

When approved, idea becomes a ticket:

```json
{
  "id": "ticket-uuid",
  "project_id": "project-uuid",
  "idea_id": "idea-uuid",
  "title": "Add multiplayer support",
  "description": "...",
  "type": "feature",
  "status": "queued",
  "priority": 2,
  "spec": {
    "requirements": ["..."],
    "research": {"..."},
    "answered_questions": [{"..."}],
    "constraints": ["..."]
  },
  "subtasks": [
    {"title": "Network layer setup", "status": "pending"},
    {"title": "Player sync system", "status": "pending"},
    {"title": "Lobby UI", "status": "pending"}
  ]
}
```

---

## UI Components

### Ideas Inbox

```
┌─────────────────────────────────────────────────────────────┐
│ IDEAS INBOX                                    [+ New Idea] │
├─────────────────────────────────────────────────────────────┤
│ Filter: [All ▼] [Pending Questions ▼]     Sort: [Newest ▼] │
├─────────────────────────────────────────────────────────────┤
│ ⏳ Add multiplayer support              2 questions pending │
│ 🔄 Improve inventory UI                        refining... │
│ ✅ Fix save corruption bug                  ready to review │
│ ❌ Remove main menu                              rejected │
└─────────────────────────────────────────────────────────────┘
```

### Question Interface

```
┌─────────────────────────────────────────────────────────────┐
│ QUESTIONS FOR: Add multiplayer support                      │
├─────────────────────────────────────────────────────────────┤
│ Question 1 of 2                                             │
│                                                             │
│ Should players share inventory or have separate inventories?│
│                                                             │
│ Context: This affects the save system architecture          │
│ significantly. Shared inventory requires conflict           │
│ resolution for simultaneous access.                         │
│                                                             │
│ ○ Shared - All players access same inventory                │
│ ● Separate - Each player has own inventory                  │
│ ○ Configurable - Host can choose                            │
│ ○ Other: [________________]                                 │
│                                                             │
│                              [Skip] [Answer & Continue →]   │
└─────────────────────────────────────────────────────────────┘
```

---

## Open Questions

| Question | Context | Decision |
|----------|---------|----------|
| Auto-approve low-risk ideas? | Speed vs control tradeoff | TBD - start manual |
| Idea templates? | Common patterns like "bug report" | TBD - good for v2 |
| Batch question answering? | Answer multiple ideas at once | TBD - UX consideration |

---

## Dependencies

- **Depends on**: 02-data-models, 03-agent-system
- **Depended by**: 05-development-pipeline, 08-web-ui

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-02-05 | Initial draft | - |
