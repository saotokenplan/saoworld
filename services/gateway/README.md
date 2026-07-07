# gateway-service

API Gateway service for the open-world AI game. Provides unified entry point, authentication, rate limiting, request tracing, and reverse proxy to all backend services.

## Features

- Unified API entry point for all clients
- JWT authentication and authorization
- Request routing and reverse proxy to backend services
- Rate limiting (token bucket)
- Request tracing (X-Request-Id, X-Trace-Id, Idempotency-Key passthrough)
- Structured logging
- Health checks (gateway + all backend services)
- Audit log persistence
- Prometheus metrics
- Alembic database migrations

## Technology Stack

- FastAPI + Uvicorn
- Pydantic + pydantic-settings
- python-jose (JWT)
- httpx (reverse proxy)
- structlog (logging)
- SQLAlchemy 2.0 (async) + PostgreSQL
- Alembic (migrations)
- Prometheus metrics
- pytest + pytest-asyncio + httpx

## Directory Structure

```
gateway-service/
├── app/
│   ├── api/              # Route handlers
│   ├── core/             # Config, database, auth, errors, limiter, proxy, metrics
│   ├── domain/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic request/response models
│   └── main.py           # FastAPI application entry point
├── alembic/              # Database migrations
│   └── versions/         # Migration scripts
├── tests/                # pytest tests
├── pyproject.toml        # Project dependencies and tool config
├── alembic.ini           # Alembic configuration
└── .env.example          # Environment variable template
```

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Copy environment file
cp .env.example .env

# Run database migrations
alembic upgrade head

# Run the service
uvicorn app.main:app --reload --port 8000

# API Docs (debug mode)
# http://localhost:8000/docs
# http://localhost:8000/redoc
```

## Configuration

Copy `.env.example` to `.env` and configure as needed.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GATEWAY_JWT_SECRET` | JWT signing secret | `change-me-in-production` |
| `GATEWAY_JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `GATEWAY_RATE_LIMIT_REQUESTS_PER_MINUTE` | Requests per minute per client | `60` |
| `GATEWAY_VOTE_SERVICE_URL` | Vote service URL | `http://localhost:8001` |
| `GATEWAY_WORLD_SERVICE_URL` | World service URL | `http://localhost:8002` |
| `GATEWAY_CONTENT_SERVICE_URL` | Content service URL | `http://localhost:8003` |
| `GATEWAY_GENERATION_SERVICE_URL` | Generation service URL | `http://localhost:8004` |
| `GATEWAY_REVIEW_SERVICE_URL` | Review service URL | `http://localhost:8005` |
| `GATEWAY_PLAYER_SERVICE_URL` | Player service URL | `http://localhost:8006` |
| `GATEWAY_OPS_SERVICE_URL` | Ops service URL | `http://localhost:8007` |

## API Routes

### Health Check

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Gateway health check |
| GET | `/api/v1/health/services` | All backend services health check |

### Proxy Routes

| Method | Path | Description |
|--------|------|-------------|
| * | `/api/v1/votes/*` | Proxy to vote-service |
| * | `/api/v1/world/*` | Proxy to world-service |
| * | `/api/v1/content/*` | Proxy to content-service |
| * | `/api/v1/generation/*` | Proxy to generation-service |
| * | `/api/v1/review/*` | Proxy to review-service |
| * | `/api/v1/player/*` | Proxy to player-service |
| * | `/api/v1/ops/*` | Proxy to ops-service |

## Running Tests

```bash
pytest
```

## Code Quality

```bash
ruff check .
mypy app
```

## Database Tables

- `audit_logs` - Audit log table

## Next Steps

- [ ] Add circuit breaker pattern for backend service failures
- [ ] Add request/response logging for proxied requests
- [ ] Add caching layer for frequently accessed GET endpoints
- [ ] Add WebSocket support for real-time features
- [ ] Add API versioning strategy
