"""公会任务系统 API 测试。"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.core.auth import create_test_token
from app.core.errors import PlayerErrorCodes
from app.domain.models import Guild, GuildMember, GuildQuest, GuildQuestProgress, Player
from app.schemas.auth import Role

PLAYER_A_ID = "00000000-0000-0000-0000-000000000001"
PLAYER_B_ID = "00000000-0000-0000-0000-000000000002"
PLAYER_C_ID = "00000000-0000-0000-0000-000000000003"


@pytest_asyncio.fixture
def player_a_token() -> str:
    return create_test_token(user_id=PLAYER_A_ID, role=Role.PLAYER)


@pytest_asyncio.fixture
def player_b_token() -> str:
    return create_test_token(user_id=PLAYER_B_ID, role=Role.PLAYER)


@pytest_asyncio.fixture
def player_c_token() -> str:
    return create_test_token(user_id=PLAYER_C_ID, role=Role.PLAYER)


@pytest_asyncio.fixture
async def player_a() -> Player:
    player = Player(
        player_id=uuid.UUID(PLAYER_A_ID),
        display_name="PlayerA",
        chapter_id="ch_prologue_01",
    )
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        session.add(player)
        await session.commit()
    return player


@pytest_asyncio.fixture
async def player_b() -> Player:
    player = Player(
        player_id=uuid.UUID(PLAYER_B_ID),
        display_name="PlayerB",
        chapter_id="ch_prologue_01",
    )
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        session.add(player)
        await session.commit()
    return player


@pytest_asyncio.fixture
async def player_c() -> Player:
    player = Player(
        player_id=uuid.UUID(PLAYER_C_ID),
        display_name="PlayerC",
        chapter_id="ch_prologue_01",
    )
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        session.add(player)
        await session.commit()
    return player


@pytest_asyncio.fixture
async def existing_guild(player_a: Player) -> Guild:
    from tests.conftest import TestSessionLocal

    guild = Guild(
        guild_id=uuid.uuid4(),
        name="TestGuild",
        leader_id=player_a.player_id,
        description="A test guild",
        level=1,
        member_count=1,
        max_members=50,
    )
    member = GuildMember(
        guild_member_id=uuid.uuid4(),
        guild_id=guild.guild_id,
        player_id=player_a.player_id,
        role="leader",
    )
    async with TestSessionLocal() as session:
        session.add(guild)
        session.add(member)
        await session.commit()
    return guild


@pytest_asyncio.fixture
async def existing_guild_with_members(player_a: Player, player_b: Player) -> Guild:
    from tests.conftest import TestSessionLocal

    guild = Guild(
        guild_id=uuid.uuid4(),
        name="MultiMemberGuild",
        leader_id=player_a.player_id,
        description="A guild with multiple members",
        level=1,
        member_count=2,
        max_members=50,
    )
    member_a = GuildMember(
        guild_member_id=uuid.uuid4(),
        guild_id=guild.guild_id,
        player_id=player_a.player_id,
        role="leader",
    )
    member_b = GuildMember(
        guild_member_id=uuid.uuid4(),
        guild_id=guild.guild_id,
        player_id=player_b.player_id,
        role="member",
    )
    async with TestSessionLocal() as session:
        session.add(guild)
        session.add(member_a)
        session.add(member_b)
        await session.commit()
    return guild


@pytest_asyncio.fixture
async def existing_guild_quest(existing_guild: Guild, player_a: Player) -> GuildQuest:
    from tests.conftest import TestSessionLocal

    quest = GuildQuest(
        guild_quest_id=uuid.uuid4(),
        guild_id=existing_guild.guild_id,
        quest_key="collect_iron",
        name="Collect Iron Ore",
        description="Collect 100 iron ore for the guild",
        quest_type="collect",
        status="active",
        objectives_jsonb={"item": "iron_ore", "target": 100},
        rewards_jsonb={"guild_exp": 500, "contribution_points": 100},
        progress_target=100,
        current_progress=30,
        time_limit_minutes=1440,
        created_by=player_a.player_id,
        schema_version=1,
    )
    async with TestSessionLocal() as session:
        session.add(quest)
        await session.commit()
    return quest


@pytest.mark.asyncio
async def test_create_guild_quest_success(
    client: AsyncClient, player_a_token: str, player_a: Player, existing_guild: Guild
) -> None:
    """测试创建公会任务成功。"""
    response = await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/quests",
        json={
            "quest_key": "kill_goblins",
            "name": "Kill Goblins",
            "description": "Kill 50 goblins",
            "quest_type": "kill",
            "objectives": {"monster": "goblin", "target": 50},
            "rewards": {"guild_exp": 300},
            "progress_target": 50,
            "time_limit_minutes": 720,
        },
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["quest_key"] == "kill_goblins"
    assert data["name"] == "Kill Goblins"
    assert data["quest_type"] == "kill"
    assert data["status"] == "active"
    assert data["progress_target"] == 50
    assert data["current_progress"] == 0


@pytest.mark.asyncio
async def test_create_guild_quest_key_exists(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    existing_guild: Guild,
    existing_guild_quest: GuildQuest,
) -> None:
    """测试创建公会任务时 key 已存在。"""
    response = await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/quests",
        json={
            "quest_key": "collect_iron",
            "name": "Another Quest",
            "description": "Another quest",
        },
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == PlayerErrorCodes.GUILD_QUEST_KEY_EXISTS


@pytest.mark.asyncio
async def test_create_guild_quest_not_leader(
    client: AsyncClient,
    player_b_token: str,
    player_b: Player,
    existing_guild: Guild,
) -> None:
    """测试非会长创建公会任务。"""
    # 先让 player_b 加入公会
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        member = GuildMember(
            guild_member_id=uuid.uuid4(),
            guild_id=existing_guild.guild_id,
            player_id=player_b.player_id,
            role="member",
        )
        session.add(member)
        await session.commit()

    response = await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/quests",
        json={
            "quest_key": "test_quest",
            "name": "Test Quest",
            "description": "A test quest",
        },
        headers={"Authorization": f"Bearer {player_b_token}"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == PlayerErrorCodes.NOT_GUILD_LEADER


@pytest.mark.asyncio
async def test_get_guild_quests_success(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    existing_guild: Guild,
    existing_guild_quest: GuildQuest,
) -> None:
    """测试获取公会任务列表成功。"""
    response = await client.get(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/quests",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert len(data["quests"]) == 1
    assert data["quests"][0]["quest_key"] == "collect_iron"
    assert data["quests"][0]["progress_percentage"] == 0.3


@pytest.mark.asyncio
async def test_get_guild_quest_detail_success(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    existing_guild: Guild,
    existing_guild_quest: GuildQuest,
) -> None:
    """测试获取公会任务详情成功。"""
    response = await client.get(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/quests/{existing_guild_quest.guild_quest_id}",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["guild_quest_id"] == str(existing_guild_quest.guild_quest_id)
    assert data["name"] == "Collect Iron Ore"


@pytest.mark.asyncio
async def test_get_guild_quest_not_found(
    client: AsyncClient, player_a_token: str, player_a: Player, existing_guild: Guild
) -> None:
    """测试获取不存在的公会任务。"""
    fake_quest_id = uuid.uuid4()
    response = await client.get(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/quests/{fake_quest_id}",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 404
    assert response.json()["code"] == PlayerErrorCodes.GUILD_QUEST_NOT_FOUND


@pytest.mark.asyncio
async def test_update_guild_quest_progress_success(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    existing_guild: Guild,
    existing_guild_quest: GuildQuest,
) -> None:
    """测试更新公会任务进度成功。"""
    response = await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/quests/{existing_guild_quest.guild_quest_id}/progress",
        json={"contribution": 20},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["guild_quest_id"] == str(existing_guild_quest.guild_quest_id)
    assert data["current_progress"] == 50


@pytest.mark.asyncio
async def test_update_guild_quest_progress_complete(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    existing_guild: Guild,
    existing_guild_quest: GuildQuest,
) -> None:
    """测试更新进度使任务完成。"""
    response = await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/quests/{existing_guild_quest.guild_quest_id}/progress",
        json={"contribution": 70},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "completed"
    assert data["current_progress"] == 100


@pytest.mark.asyncio
async def test_update_guild_quest_progress_not_active(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    existing_guild: Guild,
    existing_guild_quest: GuildQuest,
) -> None:
    """测试更新已完成任务的进度。"""
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        quest = await session.get(GuildQuest, existing_guild_quest.guild_quest_id)
        if quest:
            quest.status = "completed"
            await session.commit()

    response = await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/quests/{existing_guild_quest.guild_quest_id}/progress",
        json={"contribution": 10},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == PlayerErrorCodes.GUILD_QUEST_NOT_ACTIVE


@pytest.mark.asyncio
async def test_get_guild_quest_progress_success(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    existing_guild: Guild,
    existing_guild_quest: GuildQuest,
) -> None:
    """测试获取当前玩家的公会任务进度成功。"""
    await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/quests/{existing_guild_quest.guild_quest_id}/progress",
        json={"contribution": 20},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )

    response = await client.get(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/quests/{existing_guild_quest.guild_quest_id}/progress",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data is not None
    assert data["player_id"] == PLAYER_A_ID
    assert data["contribution"] == 20


@pytest.mark.asyncio
async def test_claim_guild_quest_reward_success(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    existing_guild: Guild,
    existing_guild_quest: GuildQuest,
) -> None:
    """测试领取公会任务奖励成功。"""
    from tests.conftest import TestSessionLocal

    await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/quests/{existing_guild_quest.guild_quest_id}/progress",
        json={"contribution": 70},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )

    async with TestSessionLocal() as session:
        quest = await session.get(GuildQuest, existing_guild_quest.guild_quest_id)
        if quest:
            quest.status = "completed"
            quest.current_progress = quest.progress_target
            await session.commit()

    response = await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/quests/{existing_guild_quest.guild_quest_id}/claim-reward",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["claimed_reward"] is True


@pytest.mark.asyncio
async def test_claim_guild_quest_reward_already_claimed(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    existing_guild: Guild,
    existing_guild_quest: GuildQuest,
) -> None:
    """测试重复领取公会任务奖励。"""
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        quest = await session.get(GuildQuest, existing_guild_quest.guild_quest_id)
        if quest:
            quest.status = "completed"
            quest.current_progress = quest.progress_target
            await session.commit()

        progress = GuildQuestProgress(
            progress_id=uuid.uuid4(),
            guild_quest_id=existing_guild_quest.guild_quest_id,
            player_id=player_a.player_id,
            contribution=30,
            claimed_reward=True,
        )
        session.add(progress)
        await session.commit()

    response = await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/quests/{existing_guild_quest.guild_quest_id}/claim-reward",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == PlayerErrorCodes.GUILD_QUEST_REWARD_ALREADY_CLAIMED


@pytest.mark.asyncio
async def test_claim_guild_quest_reward_not_completed(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    existing_guild: Guild,
    existing_guild_quest: GuildQuest,
) -> None:
    """测试未完成任务时领取奖励。"""
    await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/quests/{existing_guild_quest.guild_quest_id}/progress",
        json={"contribution": 10},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )

    response = await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/quests/{existing_guild_quest.guild_quest_id}/claim-reward",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == PlayerErrorCodes.GUILD_QUEST_NOT_ACTIVE