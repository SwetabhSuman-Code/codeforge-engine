from sqlalchemy import Column, Integer, Text, ForeignKey
from app.database.db_config import Base


class TestCase(Base):
    __tablename__ = "testcases"
    __test__ = False

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=True)
    input_data = Column(Text, nullable=True)
    expected_output = Column(Text, nullable=True)