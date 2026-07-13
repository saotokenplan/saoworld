"""公会消息 API 测试用例"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.domain.models import Guild, GuildMember, Player
from app.main import app
from app.schemas.auth import Role
from tests.conftest import TestSessionLocal, create_test_token


@pytest_asyncio.fixture
def guild_member_token() -> str:
    return create_test_token(
        user_id="00000000-0000-0000-0000-000000000002",
        role=Role.PLAYER,
    )


@pytest_asyncio.fixture
def non_member_token() -> str:
    return create_test_token(
        user_id="00000000-0000-0000-0000-000000000003",
        role=Role.PLAYER,
    )


@pytest_asyncio.fixture
async def guild_member_player() -> Player:
    player = Player(
        player_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        display_name="GuildMember",
        chapter_id="ch_prologue_01",
    )
    async with TestSessionLocal() as session:
        session.add(player)
        await session.commit()
    return player


@pytest_asyncio.fixture
async def non_member_player() -> Player:
    player = Player(
        player_id=uuid.UUID("00000000-0000-0000-0000-000000000003"),
        display_name="NonMember",
        chapter_id="ch_prologue_01",
    )
    async with TestSessionLocal() as session:
        session.add(player)
        await session.commit()
    return player


@pytest_asyncio.fixture
async def test_guild(test_player: Player) -> Guild:
    guild = Guild(
        guild_id=uuid.UUID("00000000-0000-0000-0000-000000000010"),
        name="TestGuild",
        leader_id=test_player.player_id,
        description="Test Guild Description",
        level=1,
        member_count=2,
        max_members=50,
    )
    async with TestSessionLocal() as session:
        session.add(guild)
        await session.commit()
    return guild


@pytest_asyncio.fixture
async def test_guild_member(test_guild: Guild, guild_member_player: Player) -> GuildMember:
    member = GuildMember(
        guild_member_id=uuid.uuid4(),
        guild_id=test_guild.guild_id,
        player_id=guild_member_player.player_id,
        role="member",
    )
    async with TestSessionLocal() as session:
        session.add(member)
        await session.commit()
    return member


@pytest_asyncio.fixture
async def test_guild_leader_member(test_guild: Guild, test_player: Player) -> GuildMember:
    member = GuildMember(
        guild_member_id=uuid.uuid4(),
        guild_id=test_guild.guild_id,
        player_id=test_player.player_id,
        role="leader",
    )
    async with TestSessionLocal() as session:
        session.add(member)
        await session.commit()
    return member


@pytest_asyncio.fixture
async def setup_guild_with_members(
    test_player: Player,
    guild_member_player: Player,
) -> tuple[Guild, GuildMember, GuildMember]:
    guild = Guild(
        guild_id=uuid.UUID("00000000-0000-0000-0000-000000000010"),
        name="TestGuild",
        leader_id=test_player.player_id,
        description="Test Guild",
        level=1,
        member_count=2,
        max_members=50,
    )
    leader_member = GuildMember(
        guild_member_id=uuid.uuid4(),
        guild_id=guild.guild_id,
        player_id=test_player.player_id,
        role="leader",
    )
    member_member = GuildMember(
        guild_member_id=uuid.uuid4(),
        guild_id=guild.guild_id,
        player_id=guild_member_player.player_id,
        role="member",
    )
    async with TestSessionLocal() as session:
        session.add(guild)
        session.add(leader_member)
        session.add(member_member)
        await session.commit()
    return guild, leader_member, member_member


@pytest.mark.asyncio
async def test_send_guild_message_success(
    client: AsyncClient,
    player_token: str,
    setup_guild_with_members: tuple[Guild, GuildMember, GuildMember],
):
    guild, _, _ = setup_guild_with_members
    response = await client.post(
        f"/api/v1/player/guilds/{guild.guild_id}/messages",
        headers={"Authorization": f"Bearer {player_token}"},
        json={"content": "Hello guild!"},
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["content"] == "Hello guild!"
    assert data["guild_id"] == str(guild.guild_id)
    assert data["is_read"] is False


@pytest.mark.asyncio
async def test_send_guild_message_not_in_guild(
    client: AsyncClient,
    non_member_token: str,
    test_guild: Guild,
):
    response = await client.post(
        f"/api/v1/player/guilds/{test_guild.guild_id}/messages",
        headers={"Authorization": f"Bearer {non_member_token}"},
        json={"content": "Hello guild!"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "NOT_IN_GUILD"


@pytest.mark.asyncio
async def test_send_guild_message_guild_not_found(
    client: AsyncClient,
    player_token: str,
):
    fake_guild_id = uuid.uuid4()
    response = await client.post(
        f"/api/v1/player/guilds/{fake_guild_id}/messages",
        headers={"Authorization": f"Bearer {player_token}"},
        json={"content": "Hello guild!"},
    )
    assert response.status_code == 404
    assert response.json()["code"] == "GUILD_NOT_FOUND"


@pytest.mark.asyncio
async def test_send_guild_message_empty_content(
    client: AsyncClient,
    player_token: str,
    setup_guild_with_members: tuple[Guild, GuildMember, GuildMember],
):
    guild, _, _ = setup_guild_with_members
    response = await client.post(
        f"/api/v1/player/guilds/{guild.guild_id}/messages",
        headers={"Authorization": f"Bearer {player_token}"},
        json={"content": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_guild_messages(
    client: AsyncClient,
    player_token: str,
    guild_member_token: str,
    setup_guild_with_members: tuple[Guild, GuildMember, GuildMember],
):
    guild, _, _ = setup_guild_with_members
    await client.post(
        f"/api/v1/player/guilds/{guild.guild_id}/messages",
        headers={"Authorization": f"Bearer {player_token}"},
        json={"content": "Message 1"},
    )
    await client.post(
        f"/api/v1/player/guilds/{guild.guild_id}/messages",
        headers={"Authorization": f"Bearer {guild_member_token}"},
        json={"content": "Message 2"},
    )

    response = await client.get(
        f"/api/v1/player/guilds/{guild.guild_id}/messages",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["messages"]) == 2
    assert data["messages"][0]["content"] == "Message 2"
    assert data["messages"][1]["content"] == "Message 1"


@pytest.mark.asyncio
async def test_get_guild_messages_not_in_guild(
    client: AsyncClient,
    non_member_token: str,
    test_guild: Guild,
):
    response = await client.get(
        f"/api/v1/player/guilds/{test_guild.guild_id}/messages",
        headers={"Authorization": f"Bearer {non_member_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_mark_guild_messages_read(
    client: AsyncClient,
    player_token: str,
    guild_member_token: str,
    setup_guild_with_members: tuple[Guild, GuildMember, GuildMember],
):
    guild, _, _ = setup_guild_with_members
    await client.post(
        f"/api/v1/player/guilds/{guild.guild_id}/messages",
        headers={"Authorization": f"Bearer {guild_member_token}"},
        json={"content": "Test message"},
    )

    response = await client.post(
        f"/api/v1/player/guilds/{guild.guild_id}/messages/read",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["marked_read"] == 1


@pytest.mark.asyncio
async def test_get_guild_unread_count(
    client: AsyncClient,
    player_token: str,
    guild_member_token: str,
    setup_guild_with_members: tuple[Guild, GuildMember, GuildMember],
):
    guild, _, _ = setup_guild_with_members
    await client.post(
        f"/api/v1/player/guilds/{guild.guild_id}/messages",
        headers={"Authorization": f"Bearer {guild_member_token}"},
        json={"content": "Test message"},
    )

    response = await client.get(
        f"/api/v1/player/guilds/{guild.guild_id}/messages/unread-count",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["unread_count"] == 1


@pytest.mark.asyncio
async def test_delete_own_message(
    client: AsyncClient,
    player_token: str,
    setup_guild_with_members: tuple[Guild, GuildMember, GuildMember],
):
    guild, _, _ = setup_guild_with_members
    send_response = await client.post(
        f"/api/v1/player/guilds/{guild.guild_id}/messages",
        headers={"Authorization": f"Bearer {player_token}"},
        json={"content": "To be deleted"},
    )
    message_id = send_response.json()["data"]["message_id"]

    delete_response = await client.delete(
        f"/api/v1/player/guilds/{guild.guild_id}/messages/{message_id}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert delete_response.status_code == 200


@pytest.mark.asyncio
async def test_delete_other_message_forbidden(
    client: AsyncClient,
    player_token: str,
    guild_member_token: str,
    setup_guild_with_members: tuple[Guild, GuildMember, GuildMember],
):
    guild, _, _ = setup_guild_with_members
    send_response = await client.post(
        f"/api/v1/player/guilds/{guild.guild_id}/messages",
        headers={"Authorization": f"Bearer {player_token}"},
        json={"content": "Leader's message"},
    )
    message_id = send_response.json()["data"]["message_id"]

    delete_response = await client.delete(
        f"/api/v1/player/guilds/{guild.guild_id}/messages/{message_id}",
        headers={"Authorization": f"Bearer {guild_member_token}"},
    )
    assert delete_response.status_code == 403
    assert delete_response.json()["code"] == "CANNOT_DELETE_OTHER_MESSAGE"