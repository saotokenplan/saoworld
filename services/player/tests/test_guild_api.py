"""公会系统 API 测试。"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.core.auth import create_test_token
from app.core.errors import PlayerErrorCodes
from app.domain.models import Guild, GuildMember, Player
from app.schemas.auth import Role

PLAYER_A_ID = "00000000-0000-0000-0000-000000000001"
PLAYER_B_ID = "00000000-0000-0000-0000-000000000002"
PLAYER_C_ID = "00000000-0000-0000-0000-000000000003"
PLAYER_D_ID = "00000000-0000-0000-0000-000000000004"


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
async def existing_guild(player_a: Player) -> Guild:
    """创建一个已存在的公会。"""
    from tests.conftest import TestSessionLocal

    guild = Guild(
        guild_id=uuid.uuid4(),
        name="ExistingGuild",
        leader_id=player_a.player_id,
        description="An existing guild",
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


@pytest.mark.asyncio
async def test_create_guild_success(
    client: AsyncClient, player_a_token: str, player_a: Player
) -> None:
    """测试创建公会成功。"""
    response = await client.post(
        "/api/v1/player/guilds",
        json={"name": "TestGuild", "description": "A test guild"},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "TestGuild"
    assert data["description"] == "A test guild"
    assert data["leader_id"] == PLAYER_A_ID
    assert data["member_count"] == 1


@pytest.mark.asyncio
async def test_create_guild_name_exists(
    client: AsyncClient,
    player_a_token: str,
    player_b_token: str,
    player_a: Player,
    player_b: Player,
    existing_guild: Guild,
) -> None:
    """测试创建公会名称已存在。"""
    response = await client.post(
        "/api/v1/player/guilds",
        json={"name": "ExistingGuild"},
        headers={"Authorization": f"Bearer {player_b_token}"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == PlayerErrorCodes.GUILD_NAME_EXISTS


@pytest.mark.asyncio
async def test_create_guild_already_in_guild(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    existing_guild: Guild,
) -> None:
    """测试已加入公会的玩家创建公会。"""
    response = await client.post(
        "/api/v1/player/guilds",
        json={"name": "AnotherGuild"},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == PlayerErrorCodes.ALREADY_IN_GUILD


@pytest.mark.asyncio
async def test_get_my_guild_success(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    existing_guild: Guild,
) -> None:
    """测试获取我的公会成功。"""
    response = await client.get(
        "/api/v1/player/guilds/my",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "ExistingGuild"


@pytest.mark.asyncio
async def test_get_my_guild_not_in_guild(
    client: AsyncClient, player_b_token: str, player_b: Player
) -> None:
    """测试未加入公会时获取我的公会。"""
    response = await client.get(
        "/api/v1/player/guilds/my",
        headers={"Authorization": f"Bearer {player_b_token}"},
    )
    assert response.status_code == 404
    assert response.json()["code"] == PlayerErrorCodes.NOT_IN_GUILD


@pytest.mark.asyncio
async def test_get_guild_success(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    existing_guild: Guild,
) -> None:
    """测试获取公会详情成功。"""
    response = await client.get(
        f"/api/v1/player/guilds/{existing_guild.guild_id}",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["guild_id"] == str(existing_guild.guild_id)


@pytest.mark.asyncio
async def test_get_guild_not_found(
    client: AsyncClient, player_a_token: str, player_a: Player
) -> None:
    """测试获取不存在的公会。"""
    fake_guild_id = uuid.uuid4()
    response = await client.get(
        f"/api/v1/player/guilds/{fake_guild_id}",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 404
    assert response.json()["code"] == PlayerErrorCodes.GUILD_NOT_FOUND


@pytest.mark.asyncio
async def test_update_guild_success(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    existing_guild: Guild,
) -> None:
    """测试更新公会信息成功。"""
    response = await client.put(
        f"/api/v1/player/guilds/{existing_guild.guild_id}",
        json={"announcement": "New announcement"},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["announcement"] == "New announcement"


@pytest.mark.asyncio
async def test_update_guild_not_leader(
    client: AsyncClient,
    player_b_token: str,
    player_b: Player,
    existing_guild: Guild,
) -> None:
    """测试非会长更新公会。"""
    response = await client.put(
        f"/api/v1/player/guilds/{existing_guild.guild_id}",
        json={"announcement": "Hacked"},
        headers={"Authorization": f"Bearer {player_b_token}"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == PlayerErrorCodes.NOT_GUILD_LEADER


@pytest.mark.asyncio
async def test_add_guild_member_success(
    client: AsyncClient,
    player_a_token: str,
    player_b_token: str,
    player_a: Player,
    player_b: Player,
    existing_guild: Guild,
) -> None:
    """测试邀请成员加入公会成功。"""
    response = await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/members",
        json={"player_id": PLAYER_B_ID},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["player_id"] == PLAYER_B_ID
    assert data["role"] == "member"


@pytest.mark.asyncio
async def test_add_guild_member_already_in_guild(
    client: AsyncClient,
    player_a_token: str,
    player_b_token: str,
    player_a: Player,
    player_b: Player,
    existing_guild: Guild,
) -> None:
    """测试邀请已在公会的玩家。"""
    # 先让 player_b 加入公会
    await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/members",
        json={"player_id": PLAYER_B_ID},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )

    # 再次邀请 player_b
    response = await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/members",
        json={"player_id": PLAYER_B_ID},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == PlayerErrorCodes.ALREADY_IN_GUILD


@pytest.mark.asyncio
async def test_remove_guild_member_success(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    player_b: Player,
    existing_guild: Guild,
) -> None:
    """测试移除成员成功。"""
    # 先让 player_b 加入公会
    await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/members",
        json={"player_id": PLAYER_B_ID},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )

    # 移除 player_b
    response = await client.delete(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/members/{PLAYER_B_ID}",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["removed"] is True


@pytest.mark.asyncio
async def test_remove_guild_cannot_remove_leader(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    existing_guild: Guild,
) -> None:
    """测试不能移除会长。"""
    response = await client.delete(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/members/{PLAYER_A_ID}",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == PlayerErrorCodes.CANNOT_REMOVE_LEADER


@pytest.mark.asyncio
async def test_leave_guild_success(
    client: AsyncClient,
    player_a_token: str,
    player_b_token: str,
    player_a: Player,
    player_b: Player,
    existing_guild: Guild,
) -> None:
    """测试退出公会成功。"""
    # 先让 player_b 加入公会
    await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/members",
        json={"player_id": PLAYER_B_ID},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )

    # player_b 退出公会
    response = await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/leave",
        headers={"Authorization": f"Bearer {player_b_token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["left"] is True


@pytest.mark.asyncio
async def test_leave_guild_as_leader(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    existing_guild: Guild,
) -> None:
    """测试会长不能直接退出公会。"""
    response = await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/leave",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == PlayerErrorCodes.CANNOT_LEAVE_AS_LEADER


@pytest.mark.asyncio
async def test_transfer_leader_success(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    player_b: Player,
    existing_guild: Guild,
) -> None:
    """测试转让会长成功。"""
    # 先让 player_b 加入公会
    await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/members",
        json={"player_id": PLAYER_B_ID},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )

    # 转让会长
    response = await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/transfer",
        json={"new_leader_id": PLAYER_B_ID},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["transferred"] is True


@pytest.mark.asyncio
async def test_transfer_leader_not_leader(
    client: AsyncClient,
    player_a_token: str,
    player_b_token: str,
    player_a: Player,
    player_b: Player,
    existing_guild: Guild,
) -> None:
    """测试非会长转让会长。"""
    # 先让 player_b 加入公会
    await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/members",
        json={"player_id": PLAYER_B_ID},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )

    # player_b 尝试转让会长
    response = await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/transfer",
        json={"new_leader_id": PLAYER_A_ID},
        headers={"Authorization": f"Bearer {player_b_token}"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == PlayerErrorCodes.NOT_GUILD_LEADER


@pytest.mark.asyncio
async def test_delete_guild_success(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    existing_guild: Guild,
) -> None:
    """测试解散公会成功。"""
    response = await client.delete(
        f"/api/v1/player/guilds/{existing_guild.guild_id}",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["deleted"] is True


@pytest.mark.asyncio
async def test_get_guild_members_success(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    player_b: Player,
    existing_guild: Guild,
) -> None:
    """测试获取公会成员列表成功。"""
    # 先让 player_b 加入公会
    await client.post(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/members",
        json={"player_id": PLAYER_B_ID},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )

    response = await client.get(
        f"/api/v1/player/guilds/{existing_guild.guild_id}/members",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 2
    assert len(data["members"]) == 2
    # 验证包含会长和成员
    roles = [m["role"] for m in data["members"]]
    assert "leader" in roles
    assert "member" in roles