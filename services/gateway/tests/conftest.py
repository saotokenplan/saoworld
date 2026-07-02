from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt

from app.core.config import settings
from app.main import app


def create_test_token(player_id: str, roles: list[str] = None, scopes: list[str] = None) -> str:
    payload = {
        "player_id": player_id,
        "roles": roles or ["player"],
        "scopes": scopes or ["votes:read", "votes:submit"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_expired_token(player_id: str) -> str:
    payload = {
        "player_id": player_id,
        "roles": ["player"],
        "scopes": ["votes:read"],
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
def valid_token() -> str:
    return create_test_token("00000000-0000-0000-0000-000000000001")


@pytest_asyncio.fixture
def ops_token() -> str:
    return create_test_token(
        "00000000-0000-0000-0000-000000000002",
        roles=["ops"],
        scopes=["votes:read", "votes:submit", "ops:vote-cycles:write"],
    )


@pytest_asyncio.fixture
def expired_token() -> str:
    return create_expired_token("00000000-0000-0000-0000-000000000001")


@pytest_asyncio.fixture
def invalid_token() -> str:
    return "invalid.jwt.token.here"


@pytest_asyncio.fixture(autouse=True)
def reset_rate_limiter():
    from app.core.limiter import rate_limiter

    original_limit = rate_limiter.requests_per_minute
    rate_limiter.client_requests.clear()
    yield
    rate_limiter.client_requests.clear()
    rate_limiter.requests_per_minute = original_limit