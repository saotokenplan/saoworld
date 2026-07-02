import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.auth import create_test_token
from app.core.db import Base, get_db
from app.domain.models import ContentPackage
from app.main import app
from app.schemas.auth import Role

TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testdb_content?mode=memory&cache=shared&uri=true"

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
async def content_packages() -> list[ContentPackage]:
    now = datetime.now(timezone.utc)
    packages = [
        ContentPackage(
            content_package_id=uuid.uuid4(),
            chapter_id="chapter_01",
            package_version="pkg_ch01_20260701_01",
            title="第一章内容包 - 主线",
            summary="第一章的主要内容更新",
            status="live",
            payload_jsonb={"test": "data", "chapter": 1, "type": "main"},
            released_at=now,
        ),
        ContentPackage(
            content_package_id=uuid.uuid4(),
            chapter_id="chapter_02",
            package_version="pkg_ch02_20260701_01",
            title="第二章内容包 - 新区域",
            summary="第二章的新区域探索内容",
            status="live",
            payload_jsonb={"test": "data", "chapter": 2, "type": "region"},
            released_at=now,
        ),
        ContentPackage(
            content_package_id=uuid.uuid4(),
            chapter_id="chapter_01",
            package_version="pkg_ch01_20260702_01",
            title="第一章灰度内容包",
            summary="第一章的灰度测试内容",
            status="gray",
            gray_scope_jsonb={"player_percent": 10},
            payload_jsonb={"test": "data", "chapter": 1, "type": "gray"},
            released_at=now,
        ),
        ContentPackage(
            content_package_id=uuid.uuid4(),
            chapter_id="chapter_02",
            package_version="pkg_ch02_20260703_01",
            title="第二章待发布内容包",
            summary="第二章的待发布新内容",
            status="packaged",
            payload_jsonb={"test": "data", "chapter": 2, "type": "packaged"},
        ),
        ContentPackage(
            content_package_id=uuid.uuid4(),
            chapter_id="chapter_01",
            package_version="pkg_ch01_20260625_01",
            title="第一章已回滚内容包",
            summary="第一章已回滚的历史版本",
            status="rolled_back",
            payload_jsonb={"test": "data", "chapter": 1, "type": "rolled_back"},
        ),
    ]

    async with TestSessionLocal() as session:
        for pkg in packages:
            session.add(pkg)
        await session.commit()

    return packages
