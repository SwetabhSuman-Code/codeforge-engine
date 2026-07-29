from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies.auth import get_db, require_admin
from app.models.problem_model import Problem
from app.models.user_model import User
from app.schemas.problem_schema import ProblemCreate

router = APIRouter()


@router.post("/problem")
def create_problem(
    problem: ProblemCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    new_problem = Problem(
        title=problem.title,
        description=problem.description,
        created_by=admin_user.id,
    )

    db.add(new_problem)
    db.commit()
    db.refresh(new_problem)

    return new_problem


@router.get("/problems")
def get_problems(db: Session = Depends(get_db)):
    return db.query(Problem).all()