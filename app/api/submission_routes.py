import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.dependencies.auth import get_current_user, get_db
from app.dependencies.rate_limiter import limiter
from app.models.submission_model import Submission
from app.models.user_model import User
from app.schemas.submission_schema import SubmissionCreate
from app.services.queue_service import enqueue_submission

logger = logging.getLogger("codeforge.api")

router = APIRouter()


@router.post("/submit", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("20/minute")
def submit_code(
    request: Request,
    submission: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Async submission endpoint. Saves submission with 'pending' status,
    enqueues task for execution, and returns 202 Accepted immediately.
    """
    logger.info("Submission received from user %d for problem %d", current_user.id, submission.problem_id)

    new_submission = Submission(
        problem_id=submission.problem_id,
        owner_id=current_user.id,
        language=submission.language,
        code=submission.code,
        status="pending",
        output="",
    )

    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)

    enqueue_submission(new_submission.id)

    return {
        "id": new_submission.id,
        "status": new_submission.status,
    }


@router.get("/submissions")
def get_submissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        return db.query(Submission).all()
    return db.query(Submission).filter(Submission.owner_id == current_user.id).all()


@router.get("/submissions/{submission_id}")
def get_submission_by_id(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )
    if submission.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this submission",
        )
    return {
        "id": submission.id,
        "problem_id": submission.problem_id,
        "owner_id": submission.owner_id,
        "language": submission.language,
        "code": submission.code,
        "status": submission.status,
        "output": submission.output,
    }