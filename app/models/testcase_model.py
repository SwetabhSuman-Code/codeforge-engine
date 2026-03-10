from sqlalchemy import Column, Integer, Text
from app.database.db_config import Base

class TestCase(Base):

    __tablename__ = "testcases"

    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer)
    input_data = Column(Text)
    expected_output = Column(Text)