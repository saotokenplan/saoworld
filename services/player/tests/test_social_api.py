"""社交数据聚合 API 测试。"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.core.auth import create_test_token
from app.domain.models import Friendship, Guild, GuildMember, Player, PrivateMessage
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
def no_scope_token() -> str:
    return create_test_token(
        user_id=PLAYER_A_ID,
        role=Role.PLAYER,
        scopes=[],
    )


@pytest_asyncio.fixture
async def player_a() -> Player:
    player = Player(
        player_id=uuid.UUID(PLAYER_A_ID),
        display_name="PlayerA",
        chapter_id="ch_prologue_01",
        level=5,
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
        level=10,
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
        level=8,
    )
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        session.add(player)
        await session.commit()
    return player


@pytest_asyncio.fixture
async def test_guild(player_a: Player) -> Guild:
    from tests.conftest import TestSessionLocal

    guild = Guild(
        guild_id=uuid.uuid4(),
        name="测试公会",
        leader_id=player_a.player_id,
        level=3,
        member_count=5,
    )
    async with TestSessionLocal() as session:
        session.add(guild)
        await session.commit()
        guild_member = GuildMember(
            guild_member_id=uuid.uuid4(),
            guild_id=guild.guild_id,
            player_id=player_a.player_id,
            role="leader",
        )
        session.add(guild_member)
        await session.commit()
    return guild


@pytest_asyncio.fixture
async def accepted_friendship(player_a: Player, player_b: Player) -> Friendship:
    from tests.conftest import TestSessionLocal

    friendship = Friendship(
        friendship_id=uuid.uuid4(),
        player_id=player_a.player_id,
        friend_id=player_b.player_id,
        status="accepted",
    )
    async with TestSessionLocal() as session:
        session.add(friendship)
        await session.commit()
    return friendship


@pytest_asyncio.fixture
async def unread_messages(player_a: Player, player_b: Player) -> list[PrivateMessage]:
    from tests.conftest import TestSessionLocal

    messages = []
    for i in range(3):
        msg = PrivateMessage(
            message_id=uuid.uuid4(),
            sender_id=player_b.player_id,
            receiver_id=player_a.player_id,
            content=f"测试消息 {i}",
            is_read=False,
        )
        messages.append(msg)
    async with TestSessionLocal() as session:
        for msg in messages:
            session.add(msg)
        await session.commit()
    return messages


class TestGetSocialOverview:
    """测试社交概览接口"""

    @pytest.mark.asyncio
    async def test_get_social_overview_success_with_all_data(
        self,
        client: AsyncClient,
        player_a: Player,
        player_b: Player,
        player_a_token: str,
        test_guild: Guild,
        accepted_friendship: Friendship,
        unread_messages: list[PrivateMessage],
    ):
        """测试获取社交概览成功（有公会、有好友、有未读消息）"""
        response = await client.get(
            "/api/v1/player/social/overview",
            headers={"Authorization": f"Bearer {player_a_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["friends_count"] == 1
        assert data["data"]["pending_requests"] == 0
        assert data["data"]["unread_messages"] == 3
        assert data["data"]["guild_info"]["name"] == "测试公会"
        assert data["data"]["guild_info"]["my_role"] == "leader"
        assert len(data["data"]["recent_friends"]) == 1
        assert data["data"]["recent_friends"][0]["player_name"] == "PlayerB"

    @pytest.mark.asyncio
    async def test_get_social_overview_success_no_guild(
        self,
        client: AsyncClient,
        player_a: Player,
        player_a_token: str,
    ):
        """测试获取社交概览成功（无公会）"""
        response = await client.get(
            "/api/v1/player/social/overview",
            headers={"Authorization": f"Bearer {player_a_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["friends_count"] == 0
        assert data["data"]["pending_requests"] == 0
        assert data["data"]["unread_messages"] == 0
        assert data["data"]["guild_info"] is None
        assert len(data["data"]["recent_friends"]) == 0

    @pytest.mark.asyncio
    async def test_get_social_overview_success_zero_unread(
        self,
        client: AsyncClient,
        player_a: Player,
        player_a_token: str,
    ):
        """测试未读消息数为 0"""
        response = await client.get(
            "/api/v1/player/social/overview",
            headers={"Authorization": f"Bearer {player_a_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["unread_messages"] == 0

    @pytest.mark.asyncio
    async def test_get_social_overview_success_many_friends(
        self,
        client: AsyncClient,
        player_a: Player,
        player_a_token: str,
    ):
        """测试最近好友列表正确展示（最多5个）"""
        from tests.conftest import TestSessionLocal

        friends = []
        for i in range(10):
            friend_id = uuid.uuid4()
            friend = Player(
                player_id=friend_id,
                display_name=f"Friend{i}",
                chapter_id="ch_prologue_01",
                level=i + 1,
            )
            friendship = Friendship(
                friendship_id=uuid.uuid4(),
                player_id=player_a.player_id,
                friend_id=friend_id,
                status="accepted",
            )
            friends.append((friend, friendship))

        async with TestSessionLocal() as session:
            for friend, friendship in friends:
                session.add(friend)
                session.add(friendship)
            await session.commit()

        response = await client.get(
            "/api/v1/player/social/overview",
            headers={"Authorization": f"Bearer {player_a_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["friends_count"] == 10
        assert len(data["data"]["recent_friends"]) <= 5

    @pytest.mark.asyncio
    async def test_get_social_overview_invalid_player_id(
        self,
        client: AsyncClient,
    ):
        """测试无效的玩家ID"""
        invalid_token = create_test_token(
            user_id="invalid_uuid",
            role=Role.PLAYER,
        )
        response = await client.get(
            "/api/v1/player/social/overview",
            headers={"Authorization": f"Bearer {invalid_token}"},
        )

        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_PLAYER_ID"

    @pytest.mark.asyncio
    async def test_get_social_overview_unauthorized(self, client: AsyncClient):
        """测试未授权访问"""
        response = await client.get("/api/v1/player/social/overview")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_social_overview_forbidden(
        self,
        client: AsyncClient,
        player_a: Player,
        no_scope_token: str,
    ):
        """测试无权限访问"""
        response = await client.get(
            "/api/v1/player/social/overview",
            headers={"Authorization": f"Bearer {no_scope_token}"},
        )

        assert response.status_code == 403
