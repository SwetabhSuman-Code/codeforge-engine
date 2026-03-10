from pydantic import BaseModel

class ProblemCreate(BaseModel):

    title: str
    description: str