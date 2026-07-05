import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def mock_redis():
    redis = MagicMock()
    redis.publish = AsyncMock(return_value=1)
    redis.subscribe = AsyncMock(return_value=AsyncMock())
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    return redis


@pytest.fixture(scope="session")
def mock_db_session():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = AsyncMock()
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock(return_value=AsyncMock(scalar=AsyncMock(return_value=None), scalars=AsyncMock(return_value=[]), fetchall=AsyncMock(return_value=[])))
    return session


@pytest.fixture(scope="session")
def valid_idempotency_key():
    return str(uuid.uuid4())


@pytest.fixture(scope="session")
def valid_trace_id():
    return f"trace_{uuid.uuid4().hex[:12]}"


@pytest.fixture(scope="session")
def test_player_id():
    return str(uuid.uuid4())


@pytest.fixture(scope="session")
def test_chapter_id():
    return "chapter_01"


@pytest.fixture(scope="session")
def test_vote_cycle_data():
    return {
        "chapter_id": "chapter_01",
        "title": "Test Vote Cycle",
        "description": "Test cycle for integration testing",
        "starts_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        "ends_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        "reason": "Integration test",
        "candidates": [
            {
                "title": "Candidate A",
                "description": "First candidate",
                "impact_summary": "Impact A",
                "estimated_effort": "low",
            },
            {
                "title": "Candidate B",
                "description": "Second candidate",
                "impact_summary": "Impact B",
                "estimated_effort": "medium",
            },
        ],
    }


@pytest.fixture(scope="session")
def test_content_package_data():
    return {
        "chapter_id": "chapter_01",
        "region_id": "region_test_01",
        "title": "Test Content Package",
        "summary": "Test package for integration",
        "package_version": f"pkg_test_int_{datetime.now(timezone.utc).strftime('%Y%m%d')}_01",
        "payload": {
            "schema_version": 1,
            "package_type": "region",
            "release_notes": "Test release",
        },
        "schema_version": 1,
    }


@pytest.fixture(scope="session")
def mock_user_payload():
    from services.vote.app.schemas.auth import Role, Scope, UserPayload
    return UserPayload(
        user_id=str(uuid.uuid4()),
        role=Role.OPS,
        scopes=[
            Scope.OPS_VOTE_CYCLES_WRITE,
            Scope.CONTENT_RELEASE,
            Scope.CONTENT_ROLLBACK,
            Scope.VOTES_HISTORY_READ,
            Scope.CONTENT_READ,
        ],
    )