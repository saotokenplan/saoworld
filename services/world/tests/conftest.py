import uuid
from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.auth import create_test_token
from app.core.db import Base, get_db
from app.domain.models import Region
from app.main import app
from app.schemas.auth import Role

TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testdb_world?mode=memory&cache=shared&uri=true"

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
async def visible_regions() -> list[Region]:
    regions = [
        Region(
            region_id=uuid.uuid4(),
            chapter_id="ch_prologue_01",
            title="起始城镇",
            summary="玩家冒险的起点，一个宁静的边境小镇",
            status="active",
            visible=True,
            unlock_condition_jsonb=None,
        ),
        Region(
            region_id=uuid.uuid4(),
            chapter_id="ch_prologue_01",
            title="迷雾森林",
            summary="城镇北部的神秘森林，据说其中隐藏着古老遗迹",
            status="active",
            visible=True,
            unlock_condition_jsonb={"quest": "quest_001"},
        ),
        Region(
            region_id=uuid.uuid4(),
            chapter_id="ch_02",
            title="废弃矿洞",
            summary="山脉深处的废弃矿洞，传闻中有矮人遗迹",
            status="locked",
            visible=False,
            unlock_condition_jsonb={"level": 10},
        ),
    ]

    async with TestSessionLocal() as session:
        for r in regions:
            session.add(r)
        await session.commit()

    return regions
