import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.auth import create_test_token
from app.core.db import Base, get_db
from app.domain.models import ReviewRecord
from app.main import app
from app.schemas.auth import Role

TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testdb_review?mode=memory&cache=shared&uri=true"

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
async def review_records() -> list[ReviewRecord]:
    now = datetime.now(timezone.utc)
    obj_id = uuid.uuid4()
    reviews = [
        ReviewRecord(
            review_id=uuid.uuid4(),
            object_id=obj_id,
            object_type="npc",
            review_type="consistency",
            result="pending",
            risk_level="low",
            quality_score=0.85,
            detail_jsonb={"checks": ["faction_match", "region_consistency"], "passed": True},
            trace_id="trace_review_001",
            created_at=now,
            updated_at=now,
        ),
        ReviewRecord(
            review_id=uuid.uuid4(),
            object_id=obj_id,
            object_type="npc",
            review_type="safety",
            result="pending",
            risk_level="medium",
            quality_score=0.72,
            detail_jsonb={"checks": ["sensitive_words", "age_rating"], "passed": True},
            trace_id="trace_review_002",
            created_at=now,
            updated_at=now,
        ),
        ReviewRecord(
            review_id=uuid.uuid4(),
            object_id=uuid.uuid4(),
            object_type="quest",
            review_type="balance",
            result="approved",
            risk_level="low",
            quality_score=0.9,
            detail_jsonb={"checks": ["reward_balance", "difficulty"], "passed": True},
            operator_id="reviewer_001",
            operator_role="reviewer",
            trace_id="trace_review_003",
            created_at=now,
            updated_at=now,
        ),
        ReviewRecord(
            review_id=uuid.uuid4(),
            object_id=uuid.uuid4(),
            object_type="event",
            review_type="safety",
            result="rejected",
            risk_level="high",
            quality_score=0.45,
            detail_jsonb={"checks": ["sensitive_words"], "passed": False},
            reason="Contains sensitive content",
            operator_id="reviewer_002",
            operator_role="reviewer",
            trace_id="trace_review_004",
            created_at=now,
            updated_at=now,
        ),
        ReviewRecord(
            review_id=uuid.uuid4(),
            object_id=uuid.uuid4(),
            object_type="npc",
            review_type="quality",
            result="manual_review",
            risk_level="medium",
            quality_score=0.68,
            detail_jsonb={"checks": ["similarity_check"], "passed": False},
            operator_id="reviewer_003",
            operator_role="reviewer",
            trace_id="trace_review_005",
            created_at=now,
            updated_at=now,
        ),
    ]

    async with TestSessionLocal() as session:
        for review in reviews:
            session.add(review)
        await session.commit()

    return reviews
