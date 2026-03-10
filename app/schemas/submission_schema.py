from pydantic import BaseModel

class SubmissionCreate(BaseModel):

    problem_id: int
    code: str
    language: str