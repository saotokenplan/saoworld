# vote-service

Voting microservice for the open-world AI game. Handles vote cycles, candidates, and player vote submissions.

## Tech Stack

- FastAPI 0.111+
- SQLAlchemy 2.0 (async)
- PostgreSQL (via asyncpg)
- Alembic (migrations)
- Pydantic v2
- structlog (structured logging)

## Directory Structure

```
vote-service/
├── app/
│   ├── api/              # Route handlers
│   ├── core/             # Config, database, shared utilities
│   ├── domain/           # SQLAlchemy ORM models
│   ├── repositories/     # Data access layer
│   ├── schemas/          # Pydantic request/response models
│   ├── tasks/            # Celery async tasks (future)
│   └── main.py           # FastAPI application entry point
├── tests/                # pytest tests
├── pyproject.toml        # Project dependencies and tool config
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
cd ../services/vote
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -e ".[dev]"
```

3. Copy environment file:
```bash
cp .env.example .env
```

4. Run database migrations (Alembic to be initialized):
```bash
# TODO: Initialize Alembic and run migrations
```

5. Start the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. Run tests:
```bash
pytest
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/votes/current` | Get current open vote cycle and candidates |
| POST | `/api/v1/votes/submit` | Submit a vote |

API documentation available at `/docs` when `VOTE_DEBUG=true`.

## Implemented Features (First Slice)

- [x] Project structure and dependency configuration
- [x] Health check endpoint
- [x] Data models: VoteCycle, VoteCandidate, Vote
- [x] Pydantic schemas for request/response
- [x] Vote repository with async queries
- [x] GET /votes/current (returns 404 when no open cycle)
- [x] POST /votes/submit with idempotency, state validation, duplicate vote detection
- [x] Structured logging with request_id and trace_id
- [x] Error response envelope per API spec

## Next Steps

- [ ] Initialize Alembic for database migrations
- [ ] Add integration tests with test database
- [ ] JWT authentication middleware
- [ ] Vote cycle management endpoints (for ops)
- [ ] Vote finalization/scheduling worker
- [ ] Event publishing (vote.cycle.closed, vote.result.finalized)
