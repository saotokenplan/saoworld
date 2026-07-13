"""社交数据聚合 API 测试"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import Scope


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock 数据库会话"""
    return AsyncMock()


@pytest.fixture
def mock_user():
    """Mock 用户"""
    user = MagicMock()
    user.user_id = str(uuid.uuid4())
    user.has_scope = MagicMock(return_value=True)
    return user


class TestGetSocialOverview:
    """测试社交概览接口"""

    @pytest.mark.asyncio
    async def test_get_social_overview_success_with_all_data(
        self, client: TestClient, mock_db: AsyncMock, mock_user: MagicMock
    ):
        """测试获取社交概览成功（有公会、有好友、有未读消息）"""
        player_uuid = uuid.UUID(mock_user.user_id)
        guild_uuid = uuid.uuid4()
        friend_uuid = uuid.uuid4()

        # Mock 数据
        mock_friendship = MagicMock()
        mock_friendship.friend_id = friend_uuid
        mock_friendship.created_at = "2026-07-14T12:00:00Z"

        mock_friend_player = MagicMock()
        mock_friend_player.display_name = "测试好友"
        mock_friend_player.level = 10

        mock_guild_member = MagicMock()
        mock_guild_member.guild_id = guild_uuid
        mock_guild_member.role = "member"

        mock_guild = MagicMock()
        mock_guild.guild_id = guild_uuid
        mock_guild.name = "测试公会"
        mock_guild.level = 5
        mock_guild.member_count = 20

        with (
            patch("app.api.routes.get_db", return_value=mock_db),
            patch("app.core.deps.get_current_user", return_value=mock_user),
            patch(
                "app.repositories.friend_repo.FriendRepository.get_friends",
                new_callable=AsyncMock,
                return_value=([mock_friendship], 1),
            ),
            patch(
                "app.repositories.friend_repo.FriendRepository.get_pending_requests",
                new_callable=AsyncMock,
                return_value=([], 0),
            ),
            patch(
                "app.repositories.private_message_repo.PrivateMessageRepository.get_unread_count",
                new_callable=AsyncMock,
                return_value=5,
            ),
            patch(
                "app.repositories.guild_repo.GuildRepository.get_guild_by_player",
                new_callable=AsyncMock,
                return_value=mock_guild_member,
            ),
            patch(
                "app.repositories.guild_repo.GuildRepository.get_guild_by_id",
                new_callable=AsyncMock,
                return_value=mock_guild,
            ),
            patch(
                "app.repositories.player_repo.PlayerRepository.get_player_by_id",
                new_callable=AsyncMock,
                return_value=mock_friend_player,
            ),
        ):
            response = client.get(
                "/api/v1/player/social/overview",
                headers={"Authorization": "Bearer test_token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["friends_count"] == 1
        assert data["data"]["pending_requests"] == 0
        assert data["data"]["unread_messages"] == 5
        assert data["data"]["guild_info"]["name"] == "测试公会"
        assert data["data"]["guild_info"]["my_role"] == "member"
        assert len(data["data"]["recent_friends"]) == 1

    @pytest.mark.asyncio
    async def test_get_social_overview_success_no_guild(
        self, client: TestClient, mock_db: AsyncMock, mock_user: MagicMock
    ):
        """测试获取社交概览成功（无公会）"""
        with (
            patch("app.api.routes.get_db", return_value=mock_db),
            patch("app.core.deps.get_current_user", return_value=mock_user),
            patch(
                "app.repositories.friend_repo.FriendRepository.get_friends",
                new_callable=AsyncMock,
                return_value=([], 0),
            ),
            patch(
                "app.repositories.friend_repo.FriendRepository.get_pending_requests",
                new_callable=AsyncMock,
                return_value=([], 0),
            ),
            patch(
                "app.repositories.private_message_repo.PrivateMessageRepository.get_unread_count",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch(
                "app.repositories.guild_repo.GuildRepository.get_guild_by_player",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            response = client.get(
                "/api/v1/player/social/overview",
                headers={"Authorization": "Bearer test_token"},
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
        self, client: TestClient, mock_db: AsyncMock, mock_user: MagicMock
    ):
        """测试未读消息数为 0"""
        with (
            patch("app.api.routes.get_db", return_value=mock_db),
            patch("app.core.deps.get_current_user", return_value=mock_user),
            patch(
                "app.repositories.friend_repo.FriendRepository.get_friends",
                new_callable=AsyncMock,
                return_value=([], 0),
            ),
            patch(
                "app.repositories.friend_repo.FriendRepository.get_pending_requests",
                new_callable=AsyncMock,
                return_value=([], 0),
            ),
            patch(
                "app.repositories.private_message_repo.PrivateMessageRepository.get_unread_count",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch(
                "app.repositories.guild_repo.GuildRepository.get_guild_by_player",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            response = client.get(
                "/api/v1/player/social/overview",
                headers={"Authorization": "Bearer test_token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["unread_messages"] == 0

    @pytest.mark.asyncio
    async def test_get_social_overview_success_many_friends(
        self, client: TestClient, mock_db: AsyncMock, mock_user: MagicMock
    ):
        """测试最近好友列表正确展示（最多5个）"""
        # 创建10个好友
        friendships = []
        for i in range(10):
            mock_friendship = MagicMock()
            mock_friendship.friend_id = uuid.uuid4()
            mock_friendship.created_at = f"2026-07-{14-i:02d}T12:00:00Z"
            friendships.append(mock_friendship)

        mock_friend_player = MagicMock()
        mock_friend_player.display_name = "测试好友"
        mock_friend_player.level = 10

        with (
            patch("app.api.routes.get_db", return_value=mock_db),
            patch("app.core.deps.get_current_user", return_value=mock_user),
            patch(
                "app.repositories.friend_repo.FriendRepository.get_friends",
                new_callable=AsyncMock,
                return_value=(friendships, 10),
            ),
            patch(
                "app.repositories.friend_repo.FriendRepository.get_pending_requests",
                new_callable=AsyncMock,
                return_value=([], 0),
            ),
            patch(
                "app.repositories.private_message_repo.PrivateMessageRepository.get_unread_count",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch(
                "app.repositories.guild_repo.GuildRepository.get_guild_by_player",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "app.repositories.player_repo.PlayerRepository.get_player_by_id",
                new_callable=AsyncMock,
                return_value=mock_friend_player,
            ),
        ):
            response = client.get(
                "/api/v1/player/social/overview",
                headers={"Authorization": "Bearer test_token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["friends_count"] == 10
        # 最多显示5个最近好友
        assert len(data["data"]["recent_friends"]) <= 5

    @pytest.mark.asyncio
    async def test_get_social_overview_invalid_player_id(
        self, client: TestClient, mock_db: AsyncMock
    ):
        """测试无效的玩家ID"""
        mock_user_invalid = MagicMock()
        mock_user_invalid.user_id = "invalid_uuid"
        mock_user_invalid.has_scope = MagicMock(return_value=True)

        with (
            patch("app.api.routes.get_db", return_value=mock_db),
            patch("app.core.deps.get_current_user", return_value=mock_user_invalid),
        ):
            response = client.get(
                "/api/v1/player/social/overview",
                headers={"Authorization": "Bearer test_token"},
            )

        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_PLAYER_ID"

    @pytest.mark.asyncio
    async def test_get_social_overview_unauthorized(self, client: TestClient):
        """测试未授权访问"""
        response = client.get("/api/v1/player/social/overview")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_social_overview_forbidden(
        self, client: TestClient, mock_db: AsyncMock
    ):
        """测试无权限访问"""
        mock_user_no_scope = MagicMock()
        mock_user_no_scope.user_id = str(uuid.uuid4())
        mock_user_no_scope.has_scope = MagicMock(return_value=False)

        with (
            patch("app.api.routes.get_db", return_value=mock_db),
            patch("app.core.deps.get_current_user", return_value=mock_user_no_scope),
        ):
            response = client.get(
                "/api/v1/player/social/overview",
                headers={"Authorization": "Bearer test_token"},
            )

        assert response.status_code == 403