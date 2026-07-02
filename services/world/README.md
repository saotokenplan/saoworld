# world-service

World service for the open-world AI game. Manages regions, factions, world state, and quest visibility.

## Tech Stack

- FastAPI 0.111+
- SQLAlchemy 2.0 (async)
- PostgreSQL (via asyncpg)
- Alembic (migrations)
- Pydantic v2
- structlog (structured logging)

## Directory Structure

```
world-service/
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
cd ../services/world
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -e ".[dev]"
```

3. Copy environment file:
```bash
cp .env.example .env
```

4. Start the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

5. Run tests:
```bash
pytest
```

## API Endpoints

| Method | Path | Description | Scope |
|--------|------|-------------|-------|
| GET | `/api/v1/health` | Health check | Public |
| GET | `/api/v1/world/regions` | List visible regions | `world:read` |
| GET | `/api/v1/world/regions/{region_id}` | Get region detail | `world:read` |
| POST | `/api/v1/ops/world/regions` | Create region | ops |
| POST | `/api/v1/ops/world/regions/{id}/status` | Update region status | ops |

API documentation available at `/docs` when `WORLD_DEBUG=true`.

## Implemented Features

- [x] Project structure and dependency configuration
- [x] Health check endpoint
- [x] Data model: Region
- [x] Pydantic schemas for request/response
- [x] World repository with async queries
- [x] GET /world/regions (visible regions, paginated)
- [x] GET /world/regions/{region_id} (region detail)
- [x] POST /ops/world/regions (create region)
- [x] POST /ops/world/regions/{id}/status (update region status)
- [x] JWT authentication with scope validation
- [x] Structured logging with request_id and trace_id
- [x] Unified response envelope per API spec
- [x] Audit log persistence

## Next Steps

- [ ] Initialize Alembic for database migrations
- [ ] Add quest definitions and player quest progress
- [ ] Add faction management
- [ ] Add world event system
- [ ] Add cache layer for frequently accessed world data
