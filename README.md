# ⚡ CodeForge Engine

> Production-grade Python / FastAPI online judge backend, backed by PostgreSQL, Redis + RQ, and Docker sandboxed code execution.

---

## 🚀 Features

- **FastAPI REST API**: Validated Pydantic schemas, dependency injection, CORS policy restrictions, and rate limiting.
- **Authentication & Authorization**: Stateless JWT access (~15 min) and refresh (~7 days) tokens with role-based access control (`user` vs `admin`).
- **PostgreSQL & Alembic**: Relational schema migrations managed via Alembic for `users`, `problems`, `submissions`, and `testcases`.
- **Sandboxed Execution**: Ephemeral Docker container execution with CPU/memory resource limits, `network_disabled=True`, and wall-clock timeouts for Python, C++, and Java.
- **Async Queue & Worker**: Background submission evaluation powered by Redis + RQ worker process.
- **Hardening & Security**: SlowAPI rate limiting (`/auth/login`, `/submit`), 64KB submission code size validation, and structured lifecycle logging.
- **Automated Testing & CI**: Comprehensive `pytest` integration test suite and GitHub Actions workflow.

---

## 🛠️ Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + SQLAlchemy ORM + Alembic
- **Task Queue**: Redis + RQ
- **Sandbox**: Docker Engine
- **Auth**: Passlib (Bcrypt) + PyJWT
- **Testing**: Pytest + TestClient

---

## 🚦 Quick Start

1. **Environment Setup**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. **Start Infrastructure**:
   ```bash
   docker compose -f docker/docker-compose.yml up -d
   ```

3. **Run Migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Run API Service**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **Run Background Worker**:
   ```bash
   python worker/worker.py
   ```

6. **Run Test Suite**:
   ```bash
   pytest -v
   ```
