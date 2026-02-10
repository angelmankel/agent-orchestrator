"""Job queue worker - processes async jobs from the queue."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Callable, Optional

from database import get_db
from models.base import generate_id

logger = logging.getLogger(__name__)


class JobWorker:
    """
    Processes jobs from the SQLite-backed queue.

    Usage:
        worker = JobWorker()
        worker.register("refine_idea", handle_refine_idea)
        await worker.start()
    """

    def __init__(self, poll_interval: float = 1.0):
        """Initialize the worker."""
        self.poll_interval = poll_interval
        self.handlers: dict[str, Callable] = {}
        self.running = False

    def register(self, job_type: str, handler: Callable):
        """Register a handler for a job type."""
        self.handlers[job_type] = handler
        logger.info(f"Registered handler for job type: {job_type}")

    async def start(self):
        """Start processing jobs."""
        self.running = True
        logger.info("Job worker started")

        while self.running:
            try:
                job = await self._claim_next_job()
                if job:
                    await self._process_job(job)
                else:
                    await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.exception(f"Error in job worker loop: {e}")
                await asyncio.sleep(self.poll_interval)

    async def stop(self):
        """Stop processing jobs."""
        self.running = False
        logger.info("Job worker stopped")

    async def enqueue(
        self,
        job_type: str,
        payload: dict,
        priority: int = 0,
        scheduled_at: Optional[datetime] = None,
    ) -> str:
        """Add a job to the queue."""
        db = await get_db()
        try:
            job_id = generate_id()
            scheduled = scheduled_at or datetime.utcnow()

            await db.execute(
                """
                INSERT INTO job_queue (id, job_type, payload, priority, scheduled_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (job_id, job_type, json.dumps(payload), priority, scheduled.isoformat()),
            )
            await db.commit()

            logger.info(f"Enqueued job {job_id} of type {job_type}")
            return job_id
        finally:
            await db.close()

    async def _claim_next_job(self) -> Optional[dict]:
        """Claim the next available job."""
        db = await get_db()
        try:
            now = datetime.utcnow().isoformat()

            cursor = await db.execute(
                """
                SELECT * FROM job_queue
                WHERE status = 'pending'
                  AND scheduled_at <= ?
                  AND attempts < max_attempts
                ORDER BY priority DESC, scheduled_at ASC
                LIMIT 1
                """,
                (now,),
            )
            row = await cursor.fetchone()

            if not row:
                return None

            job_id = row["id"]

            await db.execute(
                """
                UPDATE job_queue
                SET status = 'running', started_at = ?, attempts = attempts + 1
                WHERE id = ?
                """,
                (now, job_id),
            )
            await db.commit()

            return {
                "id": row["id"],
                "job_type": row["job_type"],
                "payload": json.loads(row["payload"]),
                "attempts": row["attempts"] + 1,
            }
        finally:
            await db.close()

    async def _process_job(self, job: dict):
        """Process a claimed job."""
        job_id = job["id"]
        job_type = job["job_type"]

        logger.info(f"Processing job {job_id} of type {job_type}")

        handler = self.handlers.get(job_type)
        if not handler:
            await self._fail_job(job_id, f"No handler for job type: {job_type}")
            return

        try:
            result = await handler(job["payload"])
            await self._complete_job(job_id, result)
        except Exception as e:
            logger.exception(f"Job {job_id} failed: {e}")
            await self._fail_job(job_id, str(e))

    async def _complete_job(self, job_id: str, result: Optional[dict] = None):
        """Mark a job as completed."""
        db = await get_db()
        try:
            result_json = json.dumps(result) if result else None
            await db.execute(
                """
                UPDATE job_queue
                SET status = 'done', completed_at = ?, result = ?
                WHERE id = ?
                """,
                (datetime.utcnow().isoformat(), result_json, job_id),
            )
            await db.commit()
            logger.info(f"Job {job_id} completed")
        finally:
            await db.close()

    async def _fail_job(self, job_id: str, error: str):
        """Mark a job as failed."""
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT attempts, max_attempts FROM job_queue WHERE id = ?",
                (job_id,),
            )
            row = await cursor.fetchone()

            status = "failed" if row["attempts"] >= row["max_attempts"] else "pending"

            await db.execute(
                """
                UPDATE job_queue
                SET status = ?, error = ?, completed_at = ?
                WHERE id = ?
                """,
                (status, error, datetime.utcnow().isoformat(), job_id),
            )
            await db.commit()
            logger.warning(f"Job {job_id} failed: {error} (status: {status})")
        finally:
            await db.close()
