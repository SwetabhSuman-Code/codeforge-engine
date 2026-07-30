import os

# Set test DATABASE_URL environment variable BEFORE importing app models or db_config
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL") or "sqlite:///./test_ci.db"

import pytest
from fastapi.testclient import TestClient

from app.database.db_config import Base, SessionLocal, engine
from app.dependencies.rate_limiter import limiter
import app.models.user_model
import app.models.problem_model
import app.models.submission_model
import app.models.testcase_model

from app.dependencies.auth import get_db
from app.main import app

# Disable rate limiter during pytest test suite execution in tests/conftest.py
limiter.enabled = False


@pytest.fixture(autouse=True)
def sync_queue_execution(monkeypatch):
    from worker.worker import process_submission

    def mock_enqueue(sub_id: int):
        process_submission(sub_id)
        return "test-sync"

    monkeypatch.setattr("app.api.submission_routes.enqueue_submission", mock_enqueue)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_ci.db"):
        try:
            os.remove("./test_ci.db")
        except OSError:
            pass


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
