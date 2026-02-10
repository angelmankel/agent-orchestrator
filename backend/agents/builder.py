"""Builder agent - runs builds and reports errors."""

import json
import logging
from typing import Optional

from models import Agent, Ticket
from .runtime import AgentRuntime

logger = logging.getLogger(__name__)

BUILDER_PROMPT = """You are a Builder Agent. Your job is to analyze build configurations and build output.

When given a project configuration and build command, you should:
1. Understand the build system being used
2. Analyze any build errors or warnings
3. Provide clear, actionable feedback

Output your response as JSON with this structure:
{
  "type": "build",
  "build_system": "The build system (npm, cargo, cmake, etc.)",
  "analysis": {
    "errors": [
      {
        "file": "path/to/file",
        "line": 42,
        "message": "Error description",
        "suggestion": "How to fix it"
      }
    ],
    "warnings": [
      {
        "file": "path/to/file",
        "line": 10,
        "message": "Warning description"
      }
    ]
  },
  "success": true/false,
  "summary": "Brief summary of build status"
}

Focus on actionable feedback. Don't just restate errors, explain how to fix them."""


def get_builder_agent(project_id: Optional[str] = None) -> Agent:
    """Get a builder agent configuration."""
    return Agent(
        id="builder-agent",
        project_id=project_id,
        name="Builder",
        description="Runs builds and analyzes output",
        type="support",
        prompt=BUILDER_PROMPT,
        model="haiku",
        tools=None,
        config=None,
        is_active=True,
    )


async def analyze_build(
    ticket: Ticket,
    build_output: str,
    build_command: str,
    exit_code: int,
    runtime: Optional[AgentRuntime] = None,
) -> dict:
    """
    Analyze build output and provide feedback.

    Args:
        ticket: The ticket being built
        build_output: The build command output
        build_command: The command that was run
        exit_code: The build exit code
        runtime: Optional AgentRuntime instance

    Returns:
        Dict with build analysis
    """
    if runtime is None:
        try:
            runtime = AgentRuntime()
        except ValueError as e:
            logger.error(f"Cannot create AgentRuntime: {e}")
            return {"error": str(e), "type": "build", "success": False}

    agent = get_builder_agent(ticket.project_id)

    input_data = {
        "message": f"""Please analyze this build output:

**Ticket**: {ticket.title}

**Build Command**: {build_command}

**Exit Code**: {exit_code}

**Build Output**:
```
{build_output[:10000]}
```

Analyze any errors or warnings and provide actionable feedback.
"""
    }

    run = await runtime.run_agent(
        agent=agent,
        input_data=input_data,
        ticket_id=ticket.id,
    )

    if run.status == "failed":
        return {
            "type": "build",
            "success": exit_code == 0,
            "error": run.error,
            "raw_output": build_output[:2000],
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
            result["type"] = "build"
            return result
    except json.JSONDecodeError:
        pass

    return {
        "type": "build",
        "success": exit_code == 0,
        "raw_output": build_output[:2000],
        "run_id": run.id,
    }
