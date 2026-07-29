# CodeForge Engine

**A production-grade online judge backend built with FastAPI, PostgreSQL, Redis, and Docker.**

CodeForge Engine is a self-hosted code execution and grading platform supporting Python, C++, and Java submissions. It evaluates code securely inside isolated Docker containers, queues execution asynchronously via Redis + RQ, and exposes a clean REST API protected by JWT authentication and role-based access control.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Database Migrations](#database-migrations)
- [Running the Worker](#running-the-worker)
- [Testing](#testing)
- [Security](#security)
- [CI/CD](#cicd)

---

## Overview

### What it does

- **Submit code** in Python, C++, or Java against a problem with defined test cases.
- **Execute sandboxed** — every submission runs in a network-isolated, resource-limited ephemeral Docker container.
- **Evaluate verdicts** — Accepted, Wrong Answer, Time Limit Exceeded, Runtime Error, Compilation Error.
- **Async grading** — submissions are enqueued immediately (HTTP 202), graded by a background RQ worker, and polled via status endpoint.
- **Secure by default** — JWT auth, role-based guards, per-IP rate limiting, CORS policy, and 64KB submission size cap.

### Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Primary database | PostgreSQL 16 | ACID compliance, FK referential integrity, production-ready |
| Auth tokens | Stateless JWT (access + refresh) | No server-side session state, horizontally scalable |
| Execution rollout | Sync-first, then async | Deterministic grading before introducing queue complexity |
| Code isolation | Docker container per submission | Process-level isolation with hard resource limits |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Client / API Consumer                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FastAPI Application (app/)                      │
│                                                                     │
│   ┌───────────────┐  ┌──────────────────┐  ┌────────────────────┐  │
│   │  /auth routes  │  │ /problem routes  │  │ /submit, /submissions│ │
│   │  Register      │  │ Admin-only CRUD  │  │ POST → 202 Accepted │ │
│   │  Login         │  │                  │  │ GET → poll status  │  │
│   │  Refresh       │  └──────────────────┘  └────────────────────┘  │
│   │  /me           │                                                 │
│   └───────────────┘                                                 │
│                                                                     │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │  Middleware: CORS · SlowAPI Rate Limiting · JWT Validation  │   │
│   └────────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ Enqueue job
                               ▼
┌──────────────────────────────────────────┐
│               Redis (RQ Queue)           │
└──────────────────────────┬───────────────┘
                           │ Dequeue job
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                      RQ Worker (worker/)                         │
│                                                                  │
│  pending → queued → executing → graded (verdict + output)        │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │          Docker Executor (docker/docker_executor.py)      │   │
│  │                                                           │   │
│  │  ● Ephemeral container per submission                     │   │
│  │  ● CPU quota: 50%, Memory limit: 128MB                    │   │
│  │  ● network_disabled=True                                  │   │
│  │  ● Wall-clock timeout: 5s (process fallback on no Docker) │   │
│  └───────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────┐
│     PostgreSQL 16 (via SQLAlchemy)  │
│                                     │
│  users · problems · submissions     │
│  testcases                          │
└─────────────────────────────────────┘
```

---

## API Reference

All endpoints are prefixed at `http://localhost:8000`.

### Auth

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | None | Register a new user |
| `POST` | `/auth/login` | None | Login, receive access + refresh tokens |
| `POST` | `/auth/refresh` | Refresh token | Exchange refresh token for new access token |
| `GET` | `/auth/me` | Bearer token | Get authenticated user profile |

### Problems

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/problem` | Admin JWT | Create a new problem |
| `GET` | `/problem` | Bearer token | List all problems |

### Submissions

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/submit` | Bearer token | Submit code — returns `202 Accepted` immediately |
| `GET` | `/submissions` | Bearer token | List own submissions (admin sees all) |
| `GET` | `/submissions/{id}` | Bearer token | Get submission status and execution output |

#### Submission Request Body

```json
{
  "problem_id": 1,
  "language": "python",
  "code": "print(int(input()) + int(input()))"
}
```

Supported languages: `python`, `cpp`, `java`

#### Submission Status Lifecycle

```
pending → queued → executing → Accepted | Wrong Answer | Time Limit Exceeded | Runtime Error | Compilation Error
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.11 |
| Web Framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Database | PostgreSQL 16 |
| Task Queue | Redis 7 + RQ |
| Code Execution | Docker Engine (ephemeral containers) |
| Authentication | PyJWT + Passlib (Bcrypt) |
| Validation | Pydantic v2 |
| Rate Limiting | SlowAPI |
| Testing | Pytest + HTTPX TestClient |
| CI | GitHub Actions |

---

## Project Structure

```
codeforge-engine/
│
├── app/
│   ├── main.py                    # FastAPI app factory, middleware, routers
│   ├── config.py                  # Pydantic-settings env config with validation
│   │
│   ├── api/
│   │   ├── auth_routes.py         # /auth/* endpoints
│   │   ├── problem_routes.py      # /problem endpoints
│   │   └── submission_routes.py   # /submit, /submissions/* endpoints
│   │
│   ├── models/
│   │   ├── user_model.py          # User SQLAlchemy entity
│   │   ├── problem_model.py       # Problem SQLAlchemy entity
│   │   ├── submission_model.py    # Submission SQLAlchemy entity
│   │   └── testcase_model.py      # TestCase SQLAlchemy entity
│   │
│   ├── schemas/
│   │   ├── user_schema.py         # UserCreate, UserResponse
│   │   ├── auth_schema.py         # TokenResponse, RefreshTokenRequest
│   │   └── submission_schema.py   # SubmissionCreate (with 64KB code cap)
│   │
│   ├── services/
│   │   ├── execution_service.py   # Language dispatch, TestCase grading loop
│   │   ├── evaluation_service.py  # stdout diff evaluator
│   │   └── queue_service.py       # Redis/RQ enqueue with sync fallback
│   │
│   ├── executors/
│   │   ├── python_executor.py     # Python executor wrapper
│   │   ├── cpp_executor.py        # C++ executor wrapper
│   │   └── java_executor.py       # Java executor wrapper
│   │
│   ├── dependencies/
│   │   ├── auth.py                # get_current_user, require_admin, get_db
│   │   └── rate_limiter.py        # SlowAPI limiter instance
│   │
│   ├── utils/
│   │   └── security.py            # JWT creation/decoding, bcrypt hashing
│   │
│   └── database/
│       └── db_config.py           # SQLAlchemy engine and session factory
│
├── worker/
│   └── worker.py                  # RQ background worker (grades submissions)
│
├── docker/
│   ├── docker_executor.py         # Ephemeral container sandbox execution
│   └── docker-compose.yml         # PostgreSQL 16 + Redis 7 services
│
├── alembic/
│   ├── env.py
│   ├── versions/
│   │   ├── 001_baseline_schema.py
│   │   └── 002_add_users_and_auth_fields.py
│
├── tests/
│   ├── conftest.py                # Pytest fixtures (DB, TestClient, limiter off)
│   ├── test_auth.py               # Auth register/login/refresh/me tests
│   ├── test_authz.py              # RBAC and submission ownership tests
│   └── test_grading.py            # Accepted / WA / TLE end-to-end grading tests
│
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI with Postgres + Redis services
│
├── .env.example                   # Environment variable template
├── requirements.txt               # Pinned Python dependencies
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Docker Desktop (running)
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/SwetabhSuman-Code/codeforge-engine.git
cd codeforge-engine
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your values (see Environment Variables section below)
```

### 5. Start Infrastructure (PostgreSQL + Redis)

```bash
docker compose -f docker/docker-compose.yml up -d
```

### 6. Run Migrations

```bash
alembic upgrade head
```

### 7. Start the API

```bash
uvicorn app.main:app --reload --port 8000
```

API is now live at `http://localhost:8000`.
Interactive docs available at `http://localhost:8000/docs`.

---

## Environment Variables

Copy `.env.example` to `.env` and configure the following:

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/codeforge` |
| `JWT_SECRET` | Secret key for JWT signing (≥ 32 chars) | `your-secret-key-here` |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime in minutes | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime in days | `7` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `CORS_ORIGINS` | Comma-separated allowed CORS origins | `http://localhost:3000` |

> **Never commit your `.env` file.** It is gitignored by default.

---

## Database Migrations

Migrations are managed with Alembic.

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration (after updating models)
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1
```

---

## Running the Worker

The RQ worker processes submission grading jobs from the Redis queue:

```bash
python worker/worker.py
```

The worker transitions submission status through:
```
pending → queued → executing → <verdict>
```

If Redis is unavailable, the queue service falls back to synchronous processing automatically.

---

## Testing

The test suite covers authentication, role-based authorization, and end-to-end grading pipeline verification.

```bash
# Run all tests with verbose output
pytest -v

# Run a specific test file
pytest tests/test_grading.py -v
```

**Test Coverage:**

| File | Tests | What's Covered |
|---|---|---|
| `test_auth.py` | 6 | Register, duplicate email, login, invalid credentials, token refresh, /me |
| `test_authz.py` | 4 | Non-admin cannot create problem, admin can create problem, submission owner isolation, admin cross-submission access |
| `test_grading.py` | 3 | Accepted verdict, Wrong Answer verdict, Time Limit Exceeded verdict |

**Total: 13 tests — all passing.**

---

## Security

| Control | Implementation |
|---|---|
| **Password Hashing** | Passlib with Bcrypt (cost factor 12) |
| **Access Tokens** | Short-lived JWT (15 min), HS256 signed |
| **Refresh Tokens** | Long-lived JWT (7 days), separate `type: refresh` claim |
| **Rate Limiting** | 10 req/min on `/auth/login`, 20 req/min on `/submit` (SlowAPI) |
| **Input Validation** | Pydantic v2 strict schema, 64KB max code size |
| **CORS** | Restricted to configured origins only |
| **Code Execution** | Network-isolated Docker containers, 128MB memory cap, 5s wall-clock timeout |
| **Secrets** | All secrets loaded from environment, validated at startup via `pydantic-settings` |

---

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and pull request to `main`:

1. Spins up **PostgreSQL 16** and **Redis 7** service containers
2. Installs Python dependencies from `requirements.txt`
3. Runs **Alembic migrations** to validate schema integrity
4. Runs the full **pytest** suite (13 tests)
