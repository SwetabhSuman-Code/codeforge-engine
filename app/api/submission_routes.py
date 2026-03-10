from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.db_config import SessionLocal
from app.schemas.submission_schema import SubmissionCreate
from app.models.submission_model import Submission
from app.services.execution_service import execute_submission

router = APIRouter()

def get_db():

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post("/submit")

def submit_code(submission: SubmissionCreate, db: Session = Depends(get_db)):

    result = execute_submission(submission.code)

    status = "Accepted"

    if result["error"]:
        status = "Error"

    new_submission = Submission(
        problem_id=submission.problem_id,
        language=submission.language,
        code=submission.code,
        status=status
    )

    db.add(new_submission)
    db.commit()

    return {
        "status": status,
        "output": result["output"]
    }