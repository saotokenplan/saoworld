import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db import Base, get_db
from app.domain.models import VoteCandidate, VoteCycle
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testdb?mode=memory&cache=shared&uri=true"

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
async def open_vote_cycle() -> VoteCycle:
    now = datetime.now(timezone.utc)
    cycle = VoteCycle(
        vote_cycle_id=uuid.uuid4(),
        chapter_id="ch_prologue_01",
        status="open",
        starts_at=now - timedelta(hours=1),
        ends_at=now + timedelta(hours=23),
        created_by="system",
        created_reason="MVP first vote cycle",
    )
    async with TestSessionLocal() as session:
        session.add(cycle)
        await session.flush()

        candidates = [
            VoteCandidate(
                vote_cycle_id=cycle.vote_cycle_id,
                title="探索迷雾森林",
                summary="玩家深入北部迷雾森林，揭开古老遗迹的秘密",
                description="一条探索向的主线，新增森林区域和3个NPC",
                region_scope=["forest_north"],
                risk_tags=["content_risk"],
                status="active",
            ),
            VoteCandidate(
                vote_cycle_id=cycle.vote_cycle_id,
                title="重建边境哨所",
                summary="协助村民重建被摧毁的边境哨所，开启贸易路线",
                description="一条建设向的主线，新增建造系统和商人NPC",
                region_scope=["border_outpost"],
                risk_tags=["economy_risk"],
                status="active",
            ),
            VoteCandidate(
                vote_cycle_id=cycle.vote_cycle_id,
                title="追踪暗影盗贼",
                summary="追查在城镇中行窃的神秘盗贼组织",
                description=None,
                region_scope=["town_square"],
                risk_tags=[],
                status="active",
            ),
        ]
        for c in candidates:
            session.add(c)
        await session.commit()

        await session.refresh(cycle)
        cycle.candidates = list(candidates)
        return cycle
