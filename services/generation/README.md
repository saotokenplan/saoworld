# generation-service

Generation service for the open-world AI game. Manages AI content generation requests, generated objects, skeleton validation, and state transitions.

## Tech Stack

- FastAPI 0.111+
- SQLAlchemy 2.0 (async)
- PostgreSQL (via asyncpg)
- Alembic (migrations)
- Pydantic v2
- structlog (structured logging)
- Prometheus metrics (prometheus-fastapi-instrumentator + business metrics)

## Directory Structure

```
generation-service/
├── app/
│   ├── api/              # Route handlers
│   ├── core/             # Config, database, auth, errors, metrics, event publisher, skeleton validator
│   ├── domain/           # SQLAlchemy ORM models
│   ├── repositories/     # Data access layer
│   ├── schemas/          # Pydantic request/response models
│   ├── tasks/            # Celery async tasks
│   └── main.py           # FastAPI application entry point
├── alembic/              # Database migrations
│   └── versions/         # Migration scripts
├── tests/                # pytest tests
├── pyproject.toml        # Project dependencies and tool config
├── alembic.ini           # Alembic configuration
└── .env.example          # Environment variable template
```

## Quick Start (Local Development)

1. Start PostgreSQL and Redis:
```bash
cd ../../infra
docker compose -f docker-compose.dev.yml up -d
```

2. Create virtual environment and install dependencies:
```bash
cd ../services/generation
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -e ".[dev]"
```

3. Copy environment file:
```bash
cp .env.example .env
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8003
```

6. Run tests:
```bash
pytest
```

7. Code quality checks:
```bash
ruff check .
mypy app
```

## API Endpoints

### Ops API

| Method | Path | Description | Scope/Role |
|--------|------|-------------|------------|
| GET | `/api/v1/health` | Health check | Public |
| POST | `/api/v1/ops/generation/requests` | Create generation request | ops |
| GET | `/api/v1/ops/generation/requests` | List generation requests (paginated) | ops |
| GET | `/api/v1/ops/generation/requests/{id}` | Get generation request detail | ops |
| POST | `/api/v1/ops/generation/requests/{id}/status` | Update request status | ops |
| GET | `/api/v1/ops/generation/objects` | List generated objects (paginated) | ops |
| GET | `/api/v1/ops/generation/objects/{id}` | Get generated object detail | ops |
| POST | `/api/v1/ops/generation/objects/{id}/status` | Update object status (review) | `review:approve` |

API documentation available at `/docs` when `GENERATION_DEBUG=true`.

## Implemented Features

- [x] Project structure and dependency configuration
- [x] Health check endpoint with service info
- [x] Data models: GenerationRequest, GeneratedObject, AuditLog
- [x] Pydantic schemas for request/response
- [x] Generation repository with async queries
- [x] World skeleton validation (check active skeleton exists, forbidden_tags not empty, chapter/region valid)
- [x] Generation request state machine: pending → processing → succeeded / failed_retryable → failed_permanent
- [x] Generated object state machine: pending_review → approved / rejected / needs_revision
- [x] POST /ops/generation/requests (create request with skeleton validation)
- [x] GET /ops/generation/requests (list requests, paginated)
- [x] GET /ops/generation/requests/{id} (request detail)
- [x] POST /ops/generation/requests/{id}/status (update request status)
- [x] GET /ops/generation/objects (list objects, paginated)
- [x] GET /ops/generation/objects/{id} (object detail)
- [x] POST /ops/generation/objects/{id}/status (update object status/review)
- [x] JWT authentication with scope validation
- [x] Structured logging with request_id and trace_id
- [x] Unified response envelope per API spec
- [x] Audit log persistence (audit_logs table)
- [x] Prometheus metrics (HTTP + business metrics)
- [x] Event publisher (generation.batch.completed)
- [x] Alembic database migrations

## Next Steps

- [ ] Add Celery async tasks for content generation
- [ ] Add template management
- [ ] Add batch generation support
- [ ] Add webhook/notification for generation completion
