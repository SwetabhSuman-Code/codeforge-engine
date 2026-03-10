from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.db_config import SessionLocal
from app.models.problem_model import Problem
from app.schemas.problem_schema import ProblemCreate

router = APIRouter()

def get_db():

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post("/problem")

def create_problem(problem: ProblemCreate, db: Session = Depends(get_db)):

    new_problem = Problem(
        title=problem.title,
        description=problem.description
    )

    db.add(new_problem)
    db.commit()
    db.refresh(new_problem)

    return new_problem


@router.get("/problems")

def get_problems(db: Session = Depends(get_db)):

    return db.query(Problem).all()