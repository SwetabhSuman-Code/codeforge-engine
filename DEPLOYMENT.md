# DEPLOYMENT GUIDE

> **SCOPE**: Production deployment instructions for CodeForge Engine's API, Worker, PostgreSQL, and Redis stack.

---

## 1. SERVICES

| Service | Container / Runtime | Purpose |
| :--- | :--- | :--- |
| `api` | `Dockerfile` (Uvicorn + FastAPI) | REST API server for auth, problem management, and submissions |
| `worker` | `Dockerfile.worker` (Python RQ) | Pulls jobs from Redis/RQ, runs sandboxed code inside ephemeral Docker containers | 
| `postgres` | `postgres:16-alpine` | PostgreSQL relational database system of record |
| `redis` | `redis:7-alpine` | Redis task queue broker |
| `migrator` | `Dockerfile` (Alembic) | Ephemeral init container that automatically executes database migrations |

The `worker` service requires access to the Docker daemon (`/var/run/docker.sock` mount) to launch sandboxed containers. The `api` service is kept network-isolated from Docker socket access for security.

---

## 2. REQUIRED ENVIRONMENT VARIABLES

Create a production `.env` file based on `.env.example`:

```bash
DATABASE_URL=postgresql://codeforge:your_secure_password@postgres:5432/codeforge
REDIS_URL=redis://redis:6379/0
JWT_SECRET=your_super_secret_jwt_key_must_be_at_least_32_characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=https://yourdomain.com
```

---

## 3. ONE-COMMAND PRODUCTION DEPLOYMENT

To deploy the entire production stack using Docker Compose:

```bash
docker compose -f docker/docker-compose.prod.yml up -d --build
```

This will automatically:
1. Spin up `postgres` and `redis` with health checks.
2. Run the `migrator` container to execute `alembic upgrade head`.
3. Start the `api` FastAPI server on port `8000`.
4. Start the `worker` RQ service to process code executions asynchronously.

---

## 4. PRE-DEPLOYMENT CHECKLIST

- [x] `pytest` suite passing.
- [x] Postgres healthcheck configured with explicitly passed credentials (`-U codeforge -d codeforge`).
- [x] Automatic database migrations configured in deployment stack (`migrator`).
- [x] Network-isolated Docker sandbox verified for user code execution.
- [x] CORS origins and JWT secrets configured via environment variables.
