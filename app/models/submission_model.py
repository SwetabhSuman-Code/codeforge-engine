from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.database.db_config import Base


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    language = Column(String, nullable=False)
    code = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="pending")
    output = Column(Text, nullable=True)