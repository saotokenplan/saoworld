# world-service

World service for the open-world AI game. Manages regions, factions, world state, quest visibility, and world skeleton snapshots.

## Documentation Positioning

- This README is the local entry for `world-service`: it summarizes the service scope, startup flow, and implemented capabilities.
- It does not replace the authoritative constraints in `docs/20-specs/backend-data-spec.md` and `docs/20-specs/product-spec.md`.
- API scopes, route references, and standard error behavior should be checked against `docs/30-api/`.

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
world-service/
├── app/
│   ├── api/              # Route handlers
│   ├── core/             # Config, database, auth, errors, metrics, event publisher
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
cd ../services/world
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
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
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

### Player API

| Method | Path | Description | Scope |
|--------|------|-------------|-------|
| GET | `/api/v1/health` | Health check | Public |
| GET | `/api/v1/world/regions` | List visible regions (paginated) | `world:read` |
| GET | `/api/v1/world/regions/{region_id}` | Get region detail | `world:read` |
| GET | `/api/v1/world/skeleton` | Get current world skeleton snapshot | `world:read` |

### Ops API

| Method | Path | Description | Scope/Role |
|--------|------|-------------|------------|
| POST | `/api/v1/ops/world/regions` | Create region | ops |
| POST | `/api/v1/ops/world/regions/{id}/status` | Update region status | ops |
| POST | `/api/v1/ops/world/skeleton` | Create world skeleton snapshot | ops |

API documentation available at `/docs` when `WORLD_DEBUG=true`.

## Implemented Features

- [x] Project structure and dependency configuration
- [x] Health check endpoint with service info
- [x] Data models: Region, WorldSkeleton, AuditLog
- [x] Pydantic schemas for request/response
- [x] World repository with async queries
- [x] GET /world/regions (visible regions, paginated, chapter filter)
- [x] GET /world/regions/{region_id} (region detail)
- [x] POST /ops/world/regions (create region)
- [x] POST /ops/world/regions/{id}/status (update region status)
- [x] World skeleton snapshot API (create + get current)
- [x] Region state machine: locked → active → unstable → archived
- [x] JWT authentication with scope validation
- [x] Structured logging with request_id and trace_id
- [x] Unified response envelope per API spec
- [x] Audit log persistence (audit_logs table)
- [x] Prometheus metrics (HTTP + business metrics)
- [x] Alembic database migrations

## Next Steps

- [ ] Add quest definitions and player quest progress
- [ ] Add faction management
- [ ] Add world event system
- [ ] Add cache layer for frequently accessed world data

## Related Docs

- `docs/20-specs/backend-data-spec.md` - Region, world state, and state-machine baseline
- `docs/20-specs/product-spec.md` - World-facing product scope and region expectations
- `docs/30-api/api-overview.md` - World API catalog and interface map
- `docs/30-api/api-permissions.md` - Scope requirements for world endpoints
- `docs/30-api/api-error-codes.md` - Standard API error behavior
- `docs/10-requirements/技术方案.md` - High-level architecture background for world interactions
