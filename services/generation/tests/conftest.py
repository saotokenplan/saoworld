import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.auth import create_test_token
from app.core.db import Base, get_db
from app.domain.models import GeneratedObject, GenerationRequest
from app.main import app
from app.schemas.auth import Role

TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testdb_generation?mode=memory&cache=shared&uri=true"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
def ops_token() -> str:
    return create_test_token(
        user_id="test_ops_user",
        role=Role.OPS,
    )


@pytest_asyncio.fixture
def player_token() -> str:
    return create_test_token(
        user_id="00000000-0000-0000-0000-000000000001",
        role=Role.PLAYER,
    )


@pytest_asyncio.fixture
def reviewer_token() -> str:
    return create_test_token(
        user_id="test_reviewer_user",
        role=Role.REVIEWER,
    )


@pytest_asyncio.fixture
async def generation_requests() -> list[GenerationRequest]:
    now = datetime.now(timezone.utc)
    requests_list = [
        GenerationRequest(
            request_id=uuid.uuid4(),
            template_id="tpl_npc_v2",
            input_payload_jsonb={"region": "wasteland", "count": 5},
            status="pending",
            trace_id="trace_pending_001",
            created_at=now,
            updated_at=now,
        ),
        GenerationRequest(
            request_id=uuid.uuid4(),
            template_id="tpl_quest_v1",
            input_payload_jsonb={"region": "wasteland", "quest_type": "side"},
            status="processing",
            trace_id="trace_processing_001",
            created_at=now,
            updated_at=now,
        ),
        GenerationRequest(
            request_id=uuid.uuid4(),
            template_id="tpl_npc_v2",
            input_payload_jsonb={"region": "city", "count": 3},
            status="succeeded",
            trace_id="trace_succeeded_001",
            created_at=now,
            updated_at=now,
        ),
        GenerationRequest(
            request_id=uuid.uuid4(),
            template_id="tpl_event_v1",
            input_payload_jsonb={"region": "wasteland"},
            status="failed_retryable",
            retry_count=1,
            error_message="API timeout",
            trace_id="trace_failed_retry_001",
            created_at=now,
            updated_at=now,
        ),
        GenerationRequest(
            request_id=uuid.uuid4(),
            template_id="tpl_npc_v2",
            input_payload_jsonb={"region": "forest", "count": 10},
            status="failed_permanent",
            retry_count=3,
            error_message="Invalid template",
            trace_id="trace_failed_perm_001",
            created_at=now,
            updated_at=now,
        ),
    ]

    async with TestSessionLocal() as session:
        for req in requests_list:
            session.add(req)
        await session.commit()

    return requests_list


@pytest_asyncio.fixture
async def generated_objects(generation_requests: list[GenerationRequest]) -> list[GeneratedObject]:
    now = datetime.now(timezone.utc)
    req = generation_requests[2]
    objects = [
        GeneratedObject(
            object_id=uuid.uuid4(),
            request_id=req.request_id,
            object_type="npc",
            schema_version=1,
            object_payload_jsonb={"name": "Blacksmith", "role": "merchant"},
            quality_score=0.85,
            status="pending_review",
            created_at=now,
            updated_at=now,
        ),
        GeneratedObject(
            object_id=uuid.uuid4(),
            request_id=req.request_id,
            object_type="npc",
            schema_version=1,
            object_payload_jsonb={"name": "Guard", "role": "warrior"},
            quality_score=0.9,
            status="approved",
            created_at=now,
            updated_at=now,
        ),
        GeneratedObject(
            object_id=uuid.uuid4(),
            request_id=req.request_id,
            object_type="quest",
            schema_version=1,
            object_payload_jsonb={"title": "Find the relic", "type": "side"},
            quality_score=0.7,
            status="rejected",
            created_at=now,
            updated_at=now,
        ),
        GeneratedObject(
            object_id=uuid.uuid4(),
            request_id=req.request_id,
            object_type="event",
            schema_version=1,
            object_payload_jsonb={"title": "Sandstorm", "type": "weather"},
            quality_score=0.65,
            status="needs_revision",
            created_at=now,
            updated_at=now,
        ),
    ]

    async with TestSessionLocal() as session:
        for obj in objects:
            session.add(obj)
        await session.commit()

    return objects
