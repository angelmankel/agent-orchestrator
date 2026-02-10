"""Reviewer agent - performs code review."""

import json
import logging
from typing import Optional

from models import Agent, Ticket
from .runtime import AgentRuntime

logger = logging.getLogger(__name__)

REVIEWER_PROMPT = """You are a Code Reviewer Agent. Your job is to review code changes for quality, correctness, and maintainability.

When given code changes, you should:
1. Check for correctness and potential bugs
2. Verify code follows conventions
3. Look for security issues
4. Assess readability and maintainability
5. Suggest improvements

Output your response as JSON with this structure:
{
  "type": "review",
  "summary": "Brief overall assessment",
  "verdict": "approve|request_changes|comment",
  "checklist": {
    "follows_conventions": true/false,
    "no_security_issues": true/false,
    "error_handling_present": true/false,
    "matches_ticket_scope": true/false,
    "no_unnecessary_complexity": true/false
  },
  "issues": [
    {
      "severity": "critical|major|minor|suggestion",
      "file": "path/to/file",
      "line": 42,
      "description": "What the issue is",
      "suggestion": "How to fix it"
    }
  ],
  "highlights": [
    "Good things about the code"
  ],
  "overall_quality": "high|medium|low"
}

Be constructive. Point out good things, not just problems."""


def get_reviewer_agent(project_id: Optional[str] = None) -> Agent:
    """Get a reviewer agent configuration."""
    return Agent(
        id="reviewer-agent",
        project_id=project_id,
        name="Reviewer",
        description="Reviews code for quality and correctness",
        type="support",
        prompt=REVIEWER_PROMPT,
        model="sonnet",
        tools=None,
        config=None,
        is_active=True,
    )


async def review_code(
    ticket: Ticket,
    changes: str,
    runtime: Optional[AgentRuntime] = None,
) -> dict:
    """
    Review code changes for a ticket.

    Args:
        ticket: The ticket being reviewed
        changes: Description of code changes (or diff)
        runtime: Optional AgentRuntime instance

    Returns:
        Dict with review results
    """
    if runtime is None:
        try:
            runtime = AgentRuntime()
        except ValueError as e:
            logger.error(f"Cannot create AgentRuntime: {e}")
            return {"error": str(e), "type": "review", "verdict": "comment"}

    agent = get_reviewer_agent(ticket.project_id)

    spec_str = json.dumps(ticket.spec, indent=2) if ticket.spec else "No specification"

    input_data = {
        "message": f"""Please review these code changes:

**Ticket**: {ticket.title}

**Type**: {ticket.type}

**Description**: {ticket.description}

**Specification**:
{spec_str}

**Code Changes**:
```
{changes[:15000]}
```

Review the changes and provide feedback.
"""
    }

    run = await runtime.run_agent(
        agent=agent,
        input_data=input_data,
        ticket_id=ticket.id,
    )

    if run.status == "failed":
        return {
            "type": "review",
            "verdict": "comment",
            "error": run.error,
            "summary": "Review failed to complete",
        }

    try:
        output_text = run.output.get("text", "") if run.output else ""
        json_start = output_text.find("{")
        json_end = output_text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            result = json.loads(output_text[json_start:json_end])
            result["run_id"] = run.id
            result["tokens_used"] = run.tokens_used
            result["cost_usd"] = run.cost_usd
            result["type"] = "review"
            return result
    except json.JSONDecodeError:
        pass

    return {
        "type": "review",
        "verdict": "comment",
        "summary": "Could not parse review output",
        "raw_output": run.output.get("text", "")[:2000] if run.output else "",
        "run_id": run.id,
    }
