# gateway-service

API Gateway service for the open-world AI game.

## Features

- Unified API entry point for all clients
- JWT authentication and authorization
- Request routing and proxy to backend services
- Rate limiting
- Request tracing (X-Request-Id, X-Trace-Id)
- Structured logging
- Health checks

## Technology Stack

- FastAPI + Uvicorn
- Pydantic + pydantic-settings
- python-jose (JWT)
- httpx (reverse proxy)
- structlog (logging)

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the service
uvicorn app.main:app --reload --port 8000

# API Docs (debug mode)
# http://localhost:8000/docs
```

## Configuration

Copy `.env.example` to `.env` and configure as needed.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| GATEWAY_JWT_SECRET | JWT signing secret | change-me-in-production |
| GATEWAY_JWT_ALGORITHM | JWT algorithm | HS256 |
| GATEWAY_RATE_LIMIT_REQUESTS_PER_MINUTE | Requests per minute per client | 60 |
| GATEWAY_VOTE_SERVICE_URL | Vote service URL | http://localhost:8001 |
| GATEWAY_WORLD_SERVICE_URL | World service URL | http://localhost:8002 |
| GATEWAY_CONTENT_SERVICE_URL | Content service URL | http://localhost:8003 |
| GATEWAY_GENERATION_SERVICE_URL | Generation service URL | http://localhost:8004 |
| GATEWAY_REVIEW_SERVICE_URL | Review service URL | http://localhost:8005 |

## API Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/health | Gateway health check |
| GET | /api/v1/health/services | Backend services health check |
| * | /api/v1/votes/* | Proxy to vote-service |
| * | /api/v1/world/* | Proxy to world-service |
| * | /api/v1/content/* | Proxy to content-service |
| * | /api/v1/generation/* | Proxy to generation-service |
| * | /api/v1/review/* | Proxy to review-service |

## Running Tests

```bash
pytest
```

## Code Quality

```bash
ruff check .
mypy app
```