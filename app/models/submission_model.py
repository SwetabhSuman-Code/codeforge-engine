from sqlalchemy import Column, Integer, String, Text
from app.database.db_config import Base

class Submission(Base):

    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer)
    language = Column(String)
    code = Column(Text)
    status = Column(String)
    output = Column(Text)