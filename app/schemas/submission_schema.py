from pydantic import BaseModel, Field


class SubmissionCreate(BaseModel):
    problem_id: int
    code: str = Field(
        ...,
        min_length=1,
        max_length=65536,
        description="Submission source code (max 64KB)",
    )
    language: str = Field(..., min_length=1, max_length=32)