import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.db_config import Base
from app.dependencies.rate_limiter import limiter
import app.models.user_model
import app.models.problem_model
import app.models.submission_model
import app.models.testcase_model

from app.dependencies.auth import get_db
from app.main import app
import worker.worker

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL") or "sqlite:///./test_ci.db"
connect_args = {"check_same_thread": False} if TEST_DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(TEST_DATABASE_URL, connect_args=connect_args)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

worker.worker.SessionLocal = TestingSessionLocal

# Disable rate limiter during pytest test suite execution in tests/conftest.py
limiter.enabled = False


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if "sqlite" in TEST_DATABASE_URL and os.path.exists("./test_ci.db"):
        try:
            os.remove("./test_ci.db")
        except OSError:
            pass


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
