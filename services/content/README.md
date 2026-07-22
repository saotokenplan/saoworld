# content-service

Content service for the open-world AI game. Manages content packages, gray release, full release, rollback, and version archiving.

## Documentation Positioning

- This README is the local entry for `content-service`: it summarizes the service scope, startup flow, and implemented capabilities.
- It does not replace the authoritative constraints in `docs/20-specs/backend-data-spec.md`, `docs/20-specs/product-spec.md`, and release-related specs.
- API scopes, endpoint references, and standard error behavior should be checked against `docs/30-api/`.

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
content-service/
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
├── scripts/              # Utility scripts (seed_initial_packages.py)
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
cd ../services/content
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

5. Seed initial content packages (optional):
```bash
python scripts/seed_initial_packages.py
```

6. Start the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

7. Run tests:
```bash
pytest
```

8. Code quality checks:
```bash
ruff check .
mypy app
```

## API Endpoints

### Player API

| Method | Path | Description | Scope |
|--------|------|-------------|-------|
| GET | `/api/v1/health` | Health check | Public |
| GET | `/api/v1/content/updates` | List visible content packages (paginated) | `content:read` |
| GET | `/api/v1/content/packages/{package_id}` | Get content package detail | `content:read` |

### Ops API

| Method | Path | Description | Scope |
|--------|------|-------------|-------|
| POST | `/api/v1/ops/content-packages` | Create content package | `content:release` |
| POST | `/api/v1/ops/content-packages/{id}/release` | Release content package (gray/full) | `content:release` |
| POST | `/api/v1/ops/content-packages/{id}/rollback` | Rollback content package | `content:rollback` |

API documentation available at `/docs` when `CONTENT_DEBUG=true`.

## Implemented Features

- [x] Project structure and dependency configuration
- [x] Health check endpoint with service info
- [x] Data models: ContentPackage, ReleaseRecord, RollbackRecord, AuditLog
- [x] Pydantic schemas for request/response
- [x] Content repository with async queries
- [x] Content package state machine: packaged → gray → live → archived, gray/live → rolled_back
- [x] Gray release visibility (player_ids, player_percent, region_ids)
- [x] GET /content/updates (visible packages, paginated, chapter filter)
- [x] GET /content/packages/{id} (package detail)
- [x] POST /ops/content-packages (create package)
- [x] POST /ops/content-packages/{id}/release (gray/full release)
- [x] POST /ops/content-packages/{id}/rollback (rollback package)
- [x] JWT authentication with scope validation
- [x] Structured logging with request_id and trace_id
- [x] Unified response envelope per API spec
- [x] Audit log persistence (audit_logs table)
- [x] Prometheus metrics (HTTP + business metrics)
- [x] Event publisher (content.package.released, content.package.rolled_back)
- [x] Alembic database migrations
- [x] Seed initial packages script

## Next Steps

- [ ] Add content package version diff/comparison
- [ ] Add content dependency management
- [ ] Add batch release/rollback support
- [ ] Add release schedule support

## Related Docs

- `docs/20-specs/backend-data-spec.md` - Content package data model, state machine, and async/event baseline
- `docs/20-specs/product-spec.md` - Product scope and content update expectations
- `docs/30-api/api-overview.md` - Content-related API catalog and upstream interface map
- `docs/30-api/api-permissions.md` - Scope requirements for content endpoints
- `docs/30-api/api-error-codes.md` - Standard API error and conflict semantics
- `docs/40-dev-loop/runbooks/operations/` - Gray release, full release, rollback, and deployment runbooks
