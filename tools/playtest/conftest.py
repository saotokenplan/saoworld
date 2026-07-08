import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest


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


@pytest.fixture(scope="session")
def mock_vote_repo():
    repo = MagicMock()
    repo.create_vote_cycle = AsyncMock(return_value=MagicMock(vote_cycle_id=uuid.uuid4()))
    repo.get_cycle_by_id = AsyncMock(return_value=MagicMock(
        vote_cycle_id=uuid.uuid4(),
        chapter_id="chapter_01",
        status="draft",
        starts_at=datetime.now(timezone.utc),
        ends_at=datetime.now(timezone.utc) + timedelta(hours=24),
        candidates=[],
        updated_at=datetime.now(timezone.utc),
        finalized_at=None,
        winning_candidate_id=None,
    ))
    repo.get_current_open_cycle = AsyncMock(return_value=MagicMock(
        vote_cycle_id=uuid.uuid4(),
        chapter_id="chapter_01",
        status="open",
        starts_at=datetime.now(timezone.utc),
        ends_at=datetime.now(timezone.utc) + timedelta(hours=24),
    ))
    repo.get_candidates_for_cycle = AsyncMock(return_value=[
        MagicMock(candidate_id=uuid.uuid4(), title="Candidate A", status="active"),
        MagicMock(candidate_id=uuid.uuid4(), title="Candidate B", status="active"),
    ])
    repo.get_candidate_by_id = AsyncMock(return_value=MagicMock(
        candidate_id=uuid.uuid4(),
        vote_cycle_id=uuid.uuid4(),
        status="active",
    ))
    repo.create_vote = AsyncMock(return_value=MagicMock(
        vote_id=uuid.uuid4(),
        vote_cycle_id=uuid.uuid4(),
        candidate_id=uuid.uuid4(),
        created_at=datetime.now(timezone.utc),
    ))
    repo.has_player_voted = AsyncMock(return_value=None)
    repo.vote_exists_by_idempotency_key = AsyncMock(return_value=None)
    repo.transition_cycle_status = AsyncMock(return_value=MagicMock(
        vote_cycle_id=uuid.uuid4(),
        status="open",
        updated_at=datetime.now(timezone.utc),
        winning_candidate_id=None,
    ))
    repo.tally_votes = AsyncMock(return_value={
        "winning_candidate_id": uuid.uuid4(),
        "total_votes": 100,
    })
    repo.get_open_cycle_for_chapter = AsyncMock(return_value=None)
    repo.is_valid_transition = MagicMock(return_value=True)
    repo.get_vote_history = AsyncMock(return_value=([], 0))
    return repo


@pytest.fixture(scope="session")
def mock_content_repo():
    repo = MagicMock()
    repo.create_package = AsyncMock(return_value=MagicMock(
        content_package_id=uuid.uuid4(),
        chapter_id="chapter_01",
        region_id="region_test_01",
        title="Test Content Package",
        status="packaged",
        package_version="pkg_test_01",
        gray_scope_jsonb=None,
        payload_jsonb={},
        schema_version=1,
        released_at=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    ))
    repo.get_package_by_id = AsyncMock(return_value=MagicMock(
        content_package_id=uuid.uuid4(),
        chapter_id="chapter_01",
        region_id="region_test_01",
        title="Test Content Package",
        status="packaged",
        package_version="pkg_test_01",
        gray_scope_jsonb=None,
        payload_jsonb={},
        schema_version=1,
        released_at=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    ))
    repo.release_package = AsyncMock(return_value=MagicMock(
        content_package_id=uuid.uuid4(),
        status="gray",
        released_at=datetime.now(timezone.utc),
    ))
    repo.rollback_package = AsyncMock(return_value=MagicMock(
        content_package_id=uuid.uuid4(),
        status="rolled_back",
    ))
    repo.list_visible_packages = AsyncMock(return_value=([], 0))
    return repo