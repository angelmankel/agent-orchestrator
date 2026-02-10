"""Clarifier agent - generates clarifying questions for ideas."""

import json
import logging
from typing import Optional

from models import Agent, Idea
from models.base import generate_id
from .runtime import AgentRuntime

logger = logging.getLogger(__name__)

CLARIFIER_PROMPT = """You are a Clarifier Agent. Your job is to analyze feature ideas and generate clarifying questions that will help turn vague ideas into precise specifications.

When given an idea, you should:
1. Identify ambiguous or underspecified aspects
2. Consider technical implications that need decisions
3. Think about edge cases and user experience questions
4. Generate 2-5 focused, actionable questions

Output your response as JSON with this structure:
{
  "analysis": {
    "clarity_score": 0.0-1.0,
    "strengths": ["what's clear about this idea"],
    "gaps": ["what's missing or unclear"]
  },
  "questions": [
    {
      "question": "The clarifying question",
      "context": "Why this question matters and what it affects",
      "priority": "high|medium|low"
    }
  ],
  "notes": "Any additional observations"
}

Be specific and actionable. Don't ask obvious questions. Focus on decisions that will significantly impact implementation."""


def get_clarifier_agent(project_id: Optional[str] = None) -> Agent:
    """Get or create a clarifier agent configuration."""
    return Agent(
        id="clarifier-agent",
        project_id=project_id,
        name="Clarifier",
        description="Analyzes ideas and generates clarifying questions",
        type="refinement",
        prompt=CLARIFIER_PROMPT,
        model="sonnet",
        tools=None,
        config=None,
        is_active=True,
    )


async def clarify_idea(idea: Idea, runtime: Optional[AgentRuntime] = None) -> dict:
    """
    Run the clarifier agent on an idea.

    Args:
        idea: The idea to analyze
        runtime: Optional AgentRuntime instance (creates one if not provided)

    Returns:
        Dict with analysis and questions
    """
    if runtime is None:
        runtime = AgentRuntime()

    agent = get_clarifier_agent(idea.project_id)

    input_data = {
        "message": f"""Please analyze this idea and generate clarifying questions:

**Title**: {idea.title}

**Description**: {idea.description}

**Priority**: {idea.priority}

**Additional Context**: {json.dumps(idea.metadata) if idea.metadata else "None provided"}
"""
    }

    run = await runtime.run_agent(
        agent=agent,
        input_data=input_data,
        idea_id=idea.id,
    )

    if run.status == "failed":
        logger.error(f"Clarifier failed for idea {idea.id}: {run.error}")
        return {
            "error": run.error,
            "analysis": None,
            "questions": [],
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
            return result
        else:
            return {
                "error": "Could not parse agent response as JSON",
                "raw_output": output_text,
                "analysis": None,
                "questions": [],
            }
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse clarifier output: {e}")
        return {
            "error": f"JSON parse error: {e}",
            "raw_output": run.output.get("text", "") if run.output else "",
            "analysis": None,
            "questions": [],
        }
