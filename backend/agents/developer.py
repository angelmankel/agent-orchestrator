"""Developer agent - implements tickets based on type."""

import json
import logging
from datetime import datetime
from typing import Optional

from database import get_db
from models import Agent, Ticket
from models.base import generate_id
from .runtime import AgentRuntime

logger = logging.getLogger(__name__)

DEVELOPER_PROMPTS = {
    "feature": """You are a Feature Developer Agent. Your job is to implement new features based on ticket specifications.

When given a ticket, you should:
1. Analyze the requirements and constraints
2. Design a clean implementation approach
3. Write high-quality, maintainable code
4. Include appropriate error handling
5. Follow project conventions

Output your response as JSON with this structure:
{
  "analysis": {
    "approach": "Brief description of implementation approach",
    "files_to_create": ["list of new files"],
    "files_to_modify": ["list of existing files to change"],
    "dependencies": ["any new dependencies needed"]
  },
  "implementation": {
    "steps": [
      {
        "description": "What this step does",
        "file": "path/to/file",
        "action": "create|modify",
        "code": "The code to write or changes to make"
      }
    ]
  },
  "notes": "Any additional implementation notes"
}

Focus on clean, working code. Don't over-engineer.""",

    "bugfix": """You are a Bugfix Developer Agent. Your job is to fix bugs based on ticket specifications.

When given a ticket, you should:
1. Understand the bug and its root cause
2. Identify the minimal fix required
3. Ensure the fix doesn't introduce regressions
4. Add defensive code if appropriate

Output your response as JSON with this structure:
{
  "analysis": {
    "root_cause": "What's causing the bug",
    "affected_files": ["files involved"],
    "risk_assessment": "low|medium|high"
  },
  "fix": {
    "steps": [
      {
        "description": "What this fix does",
        "file": "path/to/file",
        "action": "modify",
        "code": "The fix to apply"
      }
    ]
  },
  "verification": "How to verify the fix works",
  "notes": "Any additional notes"
}

Keep fixes minimal and focused.""",

    "refactor": """You are a Refactor Developer Agent. Your job is to improve code structure without changing behavior.

When given a ticket, you should:
1. Understand the current code structure
2. Identify specific improvements
3. Refactor incrementally
4. Preserve all existing behavior

Output your response as JSON with this structure:
{
  "analysis": {
    "current_issues": ["problems with current code"],
    "proposed_improvements": ["what will be improved"],
    "behavior_preserved": true
  },
  "refactoring": {
    "steps": [
      {
        "description": "What this refactoring does",
        "file": "path/to/file",
        "action": "modify",
        "code": "The refactored code"
      }
    ]
  },
  "notes": "Any additional notes"
}

Never change behavior, only structure.""",

    "chore": """You are a Chore Developer Agent. Your job is to handle maintenance tasks like dependency updates, configuration changes, and cleanup.

When given a ticket, you should:
1. Understand the maintenance task
2. Make minimal necessary changes
3. Document any configuration changes

Output your response as JSON with this structure:
{
  "analysis": {
    "task_type": "Type of chore",
    "scope": "What's affected"
  },
  "changes": {
    "steps": [
      {
        "description": "What this change does",
        "file": "path/to/file",
        "action": "create|modify|delete",
        "code": "The change to make"
      }
    ]
  },
  "notes": "Any additional notes"
}

Keep changes minimal and safe."""
}


def get_developer_agent(ticket_type: str, project_id: Optional[str] = None) -> Agent:
    """Get a developer agent configuration for the given ticket type."""
    prompt = DEVELOPER_PROMPTS.get(ticket_type, DEVELOPER_PROMPTS["feature"])

    return Agent(
        id=f"{ticket_type}-dev-agent",
        project_id=project_id,
        name=f"{ticket_type.title()} Developer",
        description=f"Implements {ticket_type} tickets",
        type="development",
        prompt=prompt,
        model="sonnet",
        tools=None,
        config=None,
        is_active=True,
    )


async def develop_ticket(ticket: Ticket, runtime: Optional[AgentRuntime] = None) -> dict:
    """
    Run development agent on a ticket.

    Args:
        ticket: The ticket to develop
        runtime: Optional AgentRuntime instance

    Returns:
        Dict with development results
    """
    if runtime is None:
        try:
            runtime = AgentRuntime()
        except ValueError as e:
            logger.error(f"Cannot create AgentRuntime: {e}")
            return {"error": str(e)}

    agent = get_developer_agent(ticket.type, ticket.project_id)

    spec_str = json.dumps(ticket.spec, indent=2) if ticket.spec else "No additional specification"

    input_data = {
        "message": f"""Please implement this ticket:

**Title**: {ticket.title}

**Type**: {ticket.type}

**Description**: {ticket.description}

**Priority**: {ticket.priority}

**Specification**:
{spec_str}
"""
    }

    run = await runtime.run_agent(
        agent=agent,
        input_data=input_data,
        ticket_id=ticket.id,
    )

    db = await get_db()
    try:
        cursor = await db.execute("SELECT id FROM agents WHERE id = ?", (agent.id,))
        if not await cursor.fetchone():
            await db.execute(
                """
                INSERT INTO agents (id, project_id, name, description, type, prompt, model, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (agent.id, agent.project_id, agent.name, agent.description, agent.type, agent.prompt, agent.model),
            )
            await db.commit()

        if run.status == "success" and run.output:
            result_data = {
                "development": run.output,
                "run_id": run.id,
                "tokens_used": run.tokens_used,
                "cost_usd": run.cost_usd,
            }

            await db.execute(
                """
                UPDATE tickets SET result = ?, status = 'review', updated_at = ?
                WHERE id = ?
                """,
                (json.dumps(result_data), datetime.utcnow().isoformat(), ticket.id),
            )
            await db.commit()

            return result_data
        else:
            result_data = {
                "error": run.error or "Development failed",
                "run_id": run.id,
            }

            await db.execute(
                """
                UPDATE tickets SET result = ?, status = 'blocked', updated_at = ?
                WHERE id = ?
                """,
                (json.dumps(result_data), datetime.utcnow().isoformat(), ticket.id),
            )
            await db.commit()

            return result_data
    finally:
        await db.close()
