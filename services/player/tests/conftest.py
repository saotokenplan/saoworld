import uuid
from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.auth import create_test_token
from app.core.db import Base, get_db
from app.domain.models import Player, PlayerQuest, PlayerRegion, PlayerInventory
from app.main import app
from app.schemas.auth import Role

TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testdb?mode=memory&cache=shared&uri=true"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    future=True,
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
async def test_player() -> Player:
    player = Player(
        player_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        display_name="TestPlayer",
        chapter_id="ch_prologue_01",
    )
    async with TestSessionLocal() as session:
        session.add(player)
        await session.commit()
    return player


@pytest_asyncio.fixture
async def test_player_quest(test_player: Player) -> PlayerQuest:
    player_quest = PlayerQuest(
        player_quest_id=uuid.uuid4(),
        player_id=test_player.player_id,
        quest_id="quest_rescue_01",
        status="active",
        objectives_jsonb={"objectives": [{"id": "obj1", "text": "寻找失踪的村民", "completed": True}]},
        rewards_jsonb={"gold": 100, "experience": 50, "reputation": {"iron_guard": 10}},
    )
    async with TestSessionLocal() as session:
        session.add(player_quest)
        await session.commit()
    return player_quest

@pytest_asyncio.fixture
async def test_player_quest_incomplete(test_player: Player) -> PlayerQuest:
    player_quest = PlayerQuest(
        player_quest_id=uuid.uuid4(),
        player_id=test_player.player_id,
        quest_id="quest_incomplete_01",
        status="active",
        objectives_jsonb={"objectives": [{"id": "obj1", "text": "寻找失踪的村民", "completed": False}]},
        rewards_jsonb={"gold": 100},
    )
    async with TestSessionLocal() as session:
        session.add(player_quest)
        await session.commit()
    return player_quest


@pytest_asyncio.fixture
async def test_player_region(test_player: Player) -> PlayerRegion:
    player_region = PlayerRegion(
        player_region_id=uuid.uuid4(),
        player_id=test_player.player_id,
        region_id="region_wasteland_01",
        unlocked_at=None,
        reputation=50,
    )
    async with TestSessionLocal() as session:
        session.add(player_region)
        await session.commit()
    return player_region


@pytest_asyncio.fixture
async def test_inventory_item(test_player: Player) -> PlayerInventory:
    item = PlayerInventory(
        inventory_id=uuid.uuid4(),
        player_id=test_player.player_id,
        item_key="item_health_potion_01",
        item_type="consumable",
        quantity=5,
        metadata_jsonb={"name": "治疗药水", "description": "恢复50点生命值", "heal_amount": 50},
    )
    async with TestSessionLocal() as session:
        session.add(item)
        await session.commit()
    return item