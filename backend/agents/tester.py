"""Tester agent - runs tests and reports failures."""

import json
import logging
from typing import Optional

from models import Agent, Ticket
from .runtime import AgentRuntime

logger = logging.getLogger(__name__)

TESTER_PROMPT = """You are a Tester Agent. Your job is to analyze test output and provide clear feedback.

When given test output, you should:
1. Identify passing and failing tests
2. Analyze failure messages and stack traces
3. Correlate failures with likely causes
4. Suggest fixes when possible

Output your response as JSON with this structure:
{
  "type": "test",
  "test_framework": "The test framework (pytest, jest, cargo test, etc.)",
  "summary": {
    "total": 10,
    "passed": 8,
    "failed": 2,
    "skipped": 0
  },
  "failures": [
    {
      "test_name": "test_something",
      "file": "tests/test_file.py",
      "line": 42,
      "error_type": "AssertionError",
      "message": "Expected X but got Y",
      "stack_trace": "Brief stack trace",
      "likely_cause": "What probably caused this",
      "suggested_fix": "How to fix it"
    }
  ],
  "success": true/false,
  "coverage": {
    "percentage": 85.5,
    "uncovered_files": ["file1.py", "file2.py"]
  }
}

Focus on actionable feedback. Help developers understand WHY tests failed."""


def get_tester_agent(project_id: Optional[str] = None) -> Agent:
    """Get a tester agent configuration."""
    return Agent(
        id="tester-agent",
        project_id=project_id,
        name="Tester",
        description="Runs tests and analyzes results",
        type="support",
        prompt=TESTER_PROMPT,
        model="haiku",
        tools=None,
        config=None,
        is_active=True,
    )


async def analyze_tests(
    ticket: Ticket,
    test_output: str,
    test_command: str,
    exit_code: int,
    runtime: Optional[AgentRuntime] = None,
) -> dict:
    """
    Analyze test output and provide feedback.

    Args:
        ticket: The ticket being tested
        test_output: The test command output
        test_command: The command that was run
        exit_code: The test exit code
        runtime: Optional AgentRuntime instance

    Returns:
        Dict with test analysis
    """
    if runtime is None:
        try:
            runtime = AgentRuntime()
        except ValueError as e:
            logger.error(f"Cannot create AgentRuntime: {e}")
            return {"error": str(e), "type": "test", "success": False}

    agent = get_tester_agent(ticket.project_id)

    input_data = {
        "message": f"""Please analyze this test output:

**Ticket**: {ticket.title}

**Test Command**: {test_command}

**Exit Code**: {exit_code}

**Test Output**:
```
{test_output[:10000]}
```

Analyze the results and provide actionable feedback for any failures.
"""
    }

    run = await runtime.run_agent(
        agent=agent,
        input_data=input_data,
        ticket_id=ticket.id,
    )

    if run.status == "failed":
        return {
            "type": "test",
            "success": exit_code == 0,
            "error": run.error,
            "raw_output": test_output[:2000],
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
            result["type"] = "test"
            return result
    except json.JSONDecodeError:
        pass

    return {
        "type": "test",
        "success": exit_code == 0,
        "raw_output": test_output[:2000],
        "run_id": run.id,
    }
