from sqlalchemy import Column, Integer, String, Text
from app.database.db_config import Base

class Problem(Base):

    __tablename__ = "problems"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(Text)