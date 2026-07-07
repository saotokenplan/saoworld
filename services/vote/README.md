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

4. Run database migrations (Alembic):
```bash
# Apply all pending migrations (vote core tables + audit_logs table)
alembic upgrade head
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

### Player Endpoints

| Method | Path | Scope | Description |
|--------|------|-------|-------------|
| GET | `/api/v1/health` | public | Health check |
| GET | `/api/v1/votes/current` | `votes:read` | Get current open vote cycle and candidates |
| POST | `/api/v1/votes/submit` | `votes:submit` | Submit a vote (idempotency-protected) |
| GET | `/api/v1/votes/history` | `votes:history:read` | Get historical vote results and landed content |

### Ops Endpoints

| Method | Path | Scope | Description |
|--------|------|-------|-------------|
| POST | `/api/v1/ops/vote-cycles` | `ops:vote-cycles:write` | Create a vote cycle (draft) |
| POST | `/api/v1/ops/vote-cycles/{id}/schedule` | `ops:vote-cycles:write` | Transition draft → scheduled |
| POST | `/api/v1/ops/vote-cycles/{id}/open` | `ops:vote-cycles:write` | Transition scheduled → open |
| POST | `/api/v1/ops/vote-cycles/{id}/close` | `ops:vote-cycles:write` | Close voting and tally results |
| POST | `/api/v1/ops/vote-cycles/{id}/finalize` | `ops:vote-cycles:write` | Confirm the tally result |

API documentation available at `/docs` when `VOTE_DEBUG=true`.

## Implemented Features

- [x] Project structure and dependency configuration
- [x] Health check endpoint
- [x] Data models: VoteCycle, VoteCandidate, Vote, AuditLog (with `votes_candidate_id_idx` index and `winning_candidate_id` FK)
- [x] Pydantic schemas for request/response
- [x] Vote repository with async queries
- [x] Player endpoints: `GET /votes/current`, `POST /votes/submit`, `GET /votes/history`
- [x] POST /votes/submit with idempotency key, state validation, duplicate vote detection
- [x] Ops endpoints: vote cycle create / schedule / open / close / finalize (full lifecycle)
- [x] Vote tally logic on close (weighted scoring, winning candidate marked `selected`)
- [x] Strict state machine validation (draft → scheduled → open → closed → finalized)
- [x] Single open cycle per chapter enforcement
- [x] JWT authentication with scope checks (`votes:read`, `votes:submit`, `votes:history:read`, `ops:vote-cycles:write`)
- [x] Audit log persistence to `audit_logs` table (vote submit, cycle create, state transitions)
- [x] Unified response envelope (`request_id`, `data`, `meta`, `trace_id`) per `12-api-design.md`
- [x] Structured logging with request_id and trace_id middleware
- [x] Error response envelope with standard error codes per API spec
- [x] Event publishing (vote.cycle.closed, vote.result.finalized) via event bus client
- [x] Prometheus metrics endpoint (`/metrics`) with business metrics (vote_submissions_total, vote_cycle_transitions_total, etc.)
- [x] Alembic migrations (vote core tables + audit_logs table)
- [x] Comprehensive test suite (54 test cases)

## Next Steps

- [ ] Connect to real PostgreSQL and run end-to-end runtime verification in a deployed environment
- [ ] Wire the tally result to downstream content generation pipeline via the event bus
