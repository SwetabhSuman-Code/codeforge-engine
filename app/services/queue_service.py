import logging
import multiprocessing
import sys

# Windows compatibility fix for RQ
if hasattr(multiprocessing, "get_context"):
    try:
        multiprocessing.get_context("fork")
    except ValueError:
        _orig_get_context = multiprocessing.get_context

        def _patched_get_context(method=None):
            if method == "fork":
                return _orig_get_context("spawn")
            return _orig_get_context(method)

        multiprocessing.get_context = _patched_get_context

from redis import Redis
from rq import Queue
from app.config import settings
from worker.worker import process_submission

logger = logging.getLogger("codeforge.queue")


def get_redis_connection() -> Redis:
    return Redis.from_url(settings.REDIS_URL)


def enqueue_submission(submission_id: int) -> str:
    """
    Enqueues submission to Redis + RQ queue for async processing.
    Falls back to synchronous worker execution if Redis connection fails.
    """
    logger.info("Submission %d: received -> queued", submission_id)
    try:
        redis_conn = get_redis_connection()
        queue = Queue(connection=redis_conn)
        job = queue.enqueue(process_submission, submission_id)
        return job.id
    except Exception as e:
        logger.warning(
            "Redis unavailable (%s), processing submission %d synchronously fallback",
            str(e),
            submission_id,
        )
        process_submission(submission_id)
        return "sync-fallback"