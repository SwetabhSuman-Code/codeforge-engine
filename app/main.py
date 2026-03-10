from fastapi import FastAPI
from app.database.db_config import Base, engine
from app.api.problem_routes import router as problem_router
from app.api.submission_routes import router as submission_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CodeForge Engine")

@app.get("/")
def home():
    return {"message": "CodeForge Engine Running"}

app.include_router(problem_router)
app.include_router(submission_router)