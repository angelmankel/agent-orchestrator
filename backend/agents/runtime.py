"""Agent runtime - executes agents using Claude API."""

import json
import logging
from datetime import datetime
from typing import Optional
from anthropic import Anthropic

from config import settings
from database import get_db
from models import Agent, AgentRun, RunLog
from models.base import generate_id

logger = logging.getLogger(__name__)

# Model mapping
MODEL_MAP = {
    "opus": "claude-opus-4-20250514",
    "sonnet": "claude-sonnet-4-20250514",
    "haiku": "claude-haiku-4-20250514",
}

# Token pricing (per million tokens)
PRICING = {
    "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-20250514": {"input": 0.25, "output": 1.25},
}


class AgentRuntime:
    """Executes agents using the Claude API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the runtime with an API key."""
        self.api_key = api_key or settings.anthropic_api_key
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        self.client = Anthropic(api_key=self.api_key)

    async def run_agent(
        self,
        agent: Agent,
        input_data: dict,
        ticket_id: Optional[str] = None,
        idea_id: Optional[str] = None,
    ) -> AgentRun:
        """
        Execute an agent with the given input.

        Args:
            agent: The agent configuration to run
            input_data: Input data for the agent (passed as user message)
            ticket_id: Optional ticket this run is associated with
            idea_id: Optional idea this run is associated with

        Returns:
            AgentRun with the execution results
        """
        run_id = generate_id()
        started_at = datetime.utcnow()

        model_id = MODEL_MAP.get(agent.model, settings.default_model)

        db = await get_db()
        try:
            await db.execute(
                """
                INSERT INTO agent_runs (id, agent_id, ticket_id, idea_id, status, input, started_at)
                VALUES (?, ?, ?, ?, 'running', ?, ?)
                """,
                (
                    run_id,
                    agent.id,
                    ticket_id,
                    idea_id,
                    json.dumps(input_data),
                    started_at.isoformat(),
                ),
            )
            await db.commit()

            await self._log(db, run_id, "info", "Starting agent run", {"model": model_id})

            try:
                user_message = self._format_input(input_data)

                response = self.client.messages.create(
                    model=model_id,
                    max_tokens=4096,
                    system=agent.prompt,
                    messages=[{"role": "user", "content": user_message}],
                )

                output_text = response.content[0].text if response.content else ""
                tokens_input = response.usage.input_tokens
                tokens_output = response.usage.output_tokens
                total_tokens = tokens_input + tokens_output

                pricing = PRICING.get(model_id, {"input": 0, "output": 0})
                cost = (tokens_input * pricing["input"] / 1_000_000) + (
                    tokens_output * pricing["output"] / 1_000_000
                )

                output_data = {
                    "text": output_text,
                    "stop_reason": response.stop_reason,
                }

                completed_at = datetime.utcnow()

                await db.execute(
                    """
                    UPDATE agent_runs
                    SET status = 'success', output = ?, tokens_used = ?, cost_usd = ?, completed_at = ?
                    WHERE id = ?
                    """,
                    (
                        json.dumps(output_data),
                        total_tokens,
                        cost,
                        completed_at.isoformat(),
                        run_id,
                    ),
                )

                await self._track_usage(
                    db, agent.project_id, agent.id, run_id, tokens_input, tokens_output, cost, model_id
                )

                await self._log(
                    db,
                    run_id,
                    "info",
                    "Agent run completed",
                    {"tokens": total_tokens, "cost_usd": cost},
                )

                await db.commit()

                return AgentRun(
                    id=run_id,
                    agent_id=agent.id,
                    ticket_id=ticket_id,
                    idea_id=idea_id,
                    status="success",
                    input=input_data,
                    output=output_data,
                    tokens_used=total_tokens,
                    cost_usd=cost,
                    started_at=started_at,
                    completed_at=completed_at,
                )

            except Exception as e:
                error_msg = str(e)
                logger.exception(f"Agent run failed: {error_msg}")

                await db.execute(
                    """
                    UPDATE agent_runs
                    SET status = 'failed', error = ?, completed_at = ?
                    WHERE id = ?
                    """,
                    (error_msg, datetime.utcnow().isoformat(), run_id),
                )
                await self._log(db, run_id, "error", f"Agent run failed: {error_msg}")
                await db.commit()

                return AgentRun(
                    id=run_id,
                    agent_id=agent.id,
                    ticket_id=ticket_id,
                    idea_id=idea_id,
                    status="failed",
                    input=input_data,
                    error=error_msg,
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                )

        finally:
            await db.close()

    def _format_input(self, input_data: dict) -> str:
        """Format input data as a message string."""
        if "message" in input_data:
            return input_data["message"]
        if "text" in input_data:
            return input_data["text"]
        return json.dumps(input_data, indent=2)

    async def _log(
        self,
        db,
        run_id: str,
        level: str,
        message: str,
        data: Optional[dict] = None,
    ):
        """Add a log entry for the run."""
        log_id = generate_id()
        data_json = json.dumps(data) if data else None
        await db.execute(
            """
            INSERT INTO run_logs (id, run_id, level, message, data)
            VALUES (?, ?, ?, ?, ?)
            """,
            (log_id, run_id, level, message, data_json),
        )

    async def _track_usage(
        self,
        db,
        project_id: Optional[str],
        agent_id: str,
        run_id: str,
        tokens_input: int,
        tokens_output: int,
        cost: float,
        model: str,
    ):
        """Track token usage."""
        usage_id = generate_id()
        await db.execute(
            """
            INSERT INTO usage_tracking (id, project_id, agent_id, run_id, tokens_input, tokens_output, cost_usd, model)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (usage_id, project_id, agent_id, run_id, tokens_input, tokens_output, cost, model),
        )
