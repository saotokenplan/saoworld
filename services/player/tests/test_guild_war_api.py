"""公会战 API 测试。"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.core.auth import create_test_token
from app.core.errors import PlayerErrorCodes
from app.domain.models import Guild, GuildMember, GuildWar, Player
from app.schemas.auth import Role

PLAYER_A_ID = "00000000-0000-0000-0000-000000000001"
PLAYER_B_ID = "00000000-0000-0000-0000-000000000002"
PLAYER_C_ID = "00000000-0000-0000-0000-000000000003"
PLAYER_D_ID = "00000000-0000-0000-0000-000000000004"
PLAYER_E_ID = "00000000-0000-0000-0000-000000000005"


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
def player_d_token() -> str:
    return create_test_token(user_id=PLAYER_D_ID, role=Role.PLAYER)


@pytest_asyncio.fixture
def player_e_token() -> str:
    return create_test_token(user_id=PLAYER_E_ID, role=Role.PLAYER)


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
async def player_d() -> Player:
    player = Player(
        player_id=uuid.UUID(PLAYER_D_ID),
        display_name="PlayerD",
        chapter_id="ch_prologue_01",
    )
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        session.add(player)
        await session.commit()
    return player


@pytest_asyncio.fixture
async def player_e() -> Player:
    player = Player(
        player_id=uuid.UUID(PLAYER_E_ID),
        display_name="PlayerE",
        chapter_id="ch_prologue_01",
    )
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        session.add(player)
        await session.commit()
    return player


@pytest_asyncio.fixture
async def guild_a(player_a: Player) -> Guild:
    """创建公会 A（player_a 为会长）。"""
    from tests.conftest import TestSessionLocal

    guild = Guild(
        guild_id=uuid.uuid4(),
        name="GuildA",
        leader_id=player_a.player_id,
        description="Guild A",
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
async def guild_b(player_b: Player) -> Guild:
    """创建公会 B（player_b 为会长）。"""
    from tests.conftest import TestSessionLocal

    guild = Guild(
        guild_id=uuid.uuid4(),
        name="GuildB",
        leader_id=player_b.player_id,
        description="Guild B",
        level=1,
        member_count=1,
        max_members=50,
    )
    member = GuildMember(
        guild_member_id=uuid.uuid4(),
        guild_id=guild.guild_id,
        player_id=player_b.player_id,
        role="leader",
    )
    async with TestSessionLocal() as session:
        session.add(guild)
        session.add(member)
        await session.commit()
    return guild


@pytest_asyncio.fixture
async def existing_war(guild_a: Guild, guild_b: Guild) -> GuildWar:
    """创建一个已宣战的公会战。"""
    from tests.conftest import TestSessionLocal

    war = GuildWar(
        war_id=uuid.uuid4(),
        challenger_guild_id=guild_a.guild_id,
        defender_guild_id=guild_b.guild_id,
        status="declared",
        war_type="territory",
    )
    async with TestSessionLocal() as session:
        session.add(war)
        await session.commit()
    return war


@pytest.mark.asyncio
async def test_declare_war_success(
    client: AsyncClient, player_a_token: str, player_a: Player, guild_a: Guild, guild_b: Guild
) -> None:
    """测试宣战成功。"""
    response = await client.post(
        "/api/v1/player/guild/wars",
        json={"defender_guild_id": str(guild_b.guild_id), "war_type": "territory"},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["challenger_guild_id"] == str(guild_a.guild_id)
    assert data["defender_guild_id"] == str(guild_b.guild_id)
    assert data["status"] == "declared"
    assert data["war_type"] == "territory"


@pytest.mark.asyncio
async def test_declare_war_on_self_guild(
    client: AsyncClient, player_a_token: str, player_a: Player, guild_a: Guild
) -> None:
    """测试对自身公会宣战。"""
    response = await client.post(
        "/api/v1/player/guild/wars",
        json={"defender_guild_id": str(guild_a.guild_id), "war_type": "territory"},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 400
    assert response.json()["code"] == PlayerErrorCodes.CANNOT_DECLARE_WAR_ON_SELF


@pytest.mark.asyncio
async def test_accept_war_success(
    client: AsyncClient,
    player_b_token: str,
    player_b: Player,
    guild_b: Guild,
    existing_war: GuildWar,
) -> None:
    """测试接受宣战成功。"""
    response = await client.post(
        f"/api/v1/player/guild/wars/{existing_war.war_id}/accept",
        headers={"Authorization": f"Bearer {player_b_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "accepted"


@pytest.mark.asyncio
async def test_accept_already_accepted_war(
    client: AsyncClient,
    player_b_token: str,
    player_b: Player,
    guild_b: Guild,
    existing_war: GuildWar,
) -> None:
    """测试接受已接受的宣战。"""
    # 先接受
    await client.post(
        f"/api/v1/player/guild/wars/{existing_war.war_id}/accept",
        headers={"Authorization": f"Bearer {player_b_token}"},
    )
    # 再次接受
    response = await client.post(
        f"/api/v1/player/guild/wars/{existing_war.war_id}/accept",
        headers={"Authorization": f"Bearer {player_b_token}"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == PlayerErrorCodes.GUILD_WAR_NOT_DECLARED


@pytest.mark.asyncio
async def test_cancel_war_success(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    guild_a: Guild,
    existing_war: GuildWar,
) -> None:
    """测试取消公会战成功。"""
    response = await client.post(
        f"/api/v1/player/guild/wars/{existing_war.war_id}/cancel",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "cancelled"


@pytest.mark.asyncio
async def test_get_active_wars(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    guild_a: Guild,
    existing_war: GuildWar,
) -> None:
    """测试获取进行中的战争。"""
    response = await client.get(
        "/api/v1/player/guild/wars/active",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] >= 1
    assert len(data["wars"]) >= 1


@pytest.mark.asyncio
async def test_get_war_history(
    client: AsyncClient,
    player_a_token: str,
    player_b_token: str,
    player_a: Player,
    player_b: Player,
    guild_a: Guild,
    existing_war: GuildWar,
) -> None:
    """测试获取战争历史。"""
    # 先取消战争使其进入历史
    await client.post(
        f"/api/v1/player/guild/wars/{existing_war.war_id}/cancel",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    response = await client.get(
        "/api/v1/player/guild/wars/history",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_join_war_success(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    guild_a: Guild,
    existing_war: GuildWar,
) -> None:
    """测试加入公会战成功。"""
    response = await client.post(
        f"/api/v1/player/guild/wars/{existing_war.war_id}/join",
        json={"guild_id": str(guild_a.guild_id)},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["player_id"] == PLAYER_A_ID
    assert data["guild_id"] == str(guild_a.guild_id)


@pytest.mark.asyncio
async def test_join_war_already_in(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    guild_a: Guild,
    existing_war: GuildWar,
) -> None:
    """测试重复加入公会战。"""
    # 先加入
    await client.post(
        f"/api/v1/player/guild/wars/{existing_war.war_id}/join",
        json={"guild_id": str(guild_a.guild_id)},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    # 再次加入
    response = await client.post(
        f"/api/v1/player/guild/wars/{existing_war.war_id}/join",
        json={"guild_id": str(guild_a.guild_id)},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == PlayerErrorCodes.PLAYER_ALREADY_IN_WAR


@pytest.mark.asyncio
async def test_get_war_scoreboard(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    guild_a: Guild,
    existing_war: GuildWar,
) -> None:
    """测试获取公会战记分板。"""
    # 先加入战争
    await client.post(
        f"/api/v1/player/guild/wars/{existing_war.war_id}/join",
        json={"guild_id": str(guild_a.guild_id)},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )

    response = await client.get(
        f"/api/v1/player/guild/wars/{existing_war.war_id}/scoreboard",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "challenger_participants" in data
    assert "defender_participants" in data


@pytest.mark.asyncio
async def test_complete_war(
    client: AsyncClient,
    player_a_token: str,
    player_b_token: str,
    player_a: Player,
    player_b: Player,
    guild_a: Guild,
    guild_b: Guild,
    existing_war: GuildWar,
) -> None:
    """测试完成公会战。"""
    # 先接受 -> 然后开始（手动修改状态模拟开始）
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        from sqlalchemy import select
        from app.domain.models import GuildWar

        stmt = select(GuildWar).where(GuildWar.war_id == existing_war.war_id)
        result = await session.execute(stmt)
        war = result.scalar_one_or_none()
        if war is not None:
            war.status = "in_progress"
            war.accepted_at = war.declared_at
            war.started_at = war.declared_at
            await session.commit()

    response = await client.post(
        f"/api/v1/player/guild/wars/{existing_war.war_id}/complete?winner_guild_id={guild_a.guild_id}",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "completed"
    assert data["winner_guild_id"] == str(guild_a.guild_id)


@pytest.mark.asyncio
async def test_war_not_found(
    client: AsyncClient, player_a_token: str, player_a: Player
) -> None:
    """测试公会战不存在。"""
    fake_war_id = uuid.uuid4()
    response = await client.get(
        f"/api/v1/player/guild/wars/{fake_war_id}",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 404
    assert response.json()["code"] == PlayerErrorCodes.GUILD_WAR_NOT_FOUND


@pytest.mark.asyncio
async def test_permission_denied_not_leader(
    client: AsyncClient,
    player_c_token: str,
    player_c: Player,
    guild_a: Guild,
    guild_b: Guild,
) -> None:
    """测试非会长/官员宣战被拒绝。"""
    # player_c 不在任何公会
    response = await client.post(
        "/api/v1/player/guild/wars",
        json={"defender_guild_id": str(guild_b.guild_id), "war_type": "territory"},
        headers={"Authorization": f"Bearer {player_c_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_war_details(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    existing_war: GuildWar,
) -> None:
    """测试获取公会战详情。"""
    response = await client.get(
        f"/api/v1/player/guild/wars/{existing_war.war_id}",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["war_id"] == str(existing_war.war_id)
    assert data["war_type"] == "territory"


@pytest.mark.asyncio
async def test_list_pagination(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    guild_a: Guild,
    guild_b: Guild,
) -> None:
    """测试战争列表分页。"""
    # 创建2场战争
    await client.post(
        "/api/v1/player/guild/wars",
        json={"defender_guild_id": str(guild_b.guild_id), "war_type": "territory"},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )

    response = await client.get(
        "/api/v1/player/guild/wars/active?limit=1&offset=0",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["wars"]) <= 1
    assert "total" in data
