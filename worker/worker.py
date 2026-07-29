import logging
import multiprocessing
import os
import sys

# Ensure app package is importable when running worker from worker/ directory
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

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
from rq import Queue, Worker
from app.config import settings
from app.database.db_config import SessionLocal
from app.models.submission_model import Submission
from app.services.execution_service import execute_submission

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("codeforge.worker")


def process_submission(submission_id: int):
    """
    Worker task: reads submission from DB, updates status to 'executing',
    runs execution/grading pipeline, and writes back the final verdict & output.
    """
    logger.info("Submission %d: queued -> executing", submission_id)

    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            logger.error("Submission %d not found in database", submission_id)
            return

        submission.status = "executing"
        db.commit()

        result = execute_submission(
            language=submission.language,
            code=submission.code,
            problem_id=submission.problem_id,
            db=db,
        )

        verdict = result.get("verdict", "Accepted")
        output = result.get("output", "")

        submission.status = verdict
        submission.output = output
        db.commit()

        logger.info(
            "Submission %d: executing -> graded (%s)", submission_id, verdict
        )
    except Exception as e:
        logger.exception("Error processing submission %d: %s", submission_id, str(e))
        if "submission" in locals() and submission:
            submission.status = "Runtime Error"
            submission.output = f"Internal worker processing error: {str(e)}"
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    redis_conn = Redis.from_url(settings.REDIS_URL)
    queue = Queue(connection=redis_conn)
    logger.info("Starting CodeForge Engine worker listening on default queue...")
    worker = Worker([queue], connection=redis_conn)
    worker.work()