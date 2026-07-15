"""私聊消息 API 测试。"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_test_token
from app.domain.models import Friendship, Player, PrivateMessage
from app.schemas.auth import Role, Scope


@pytest.fixture
def player_a_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def player_b_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def player_c_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000003")


@pytest.fixture
def player_a_headers(player_a_id: uuid.UUID) -> dict[str, str]:
    token = create_test_token(
        user_id=str(player_a_id),
        role=Role.PLAYER,
        scopes=[Scope.MESSAGES_READ, Scope.MESSAGES_WRITE, Scope.FRIENDS_READ, Scope.FRIENDS_WRITE],
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def player_b_headers(player_b_id: uuid.UUID) -> dict[str, str]:
    token = create_test_token(
        user_id=str(player_b_id),
        role=Role.PLAYER,
        scopes=[Scope.MESSAGES_READ, Scope.MESSAGES_WRITE, Scope.FRIENDS_READ, Scope.FRIENDS_WRITE],
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def player_c_headers(player_c_id: uuid.UUID) -> dict[str, str]:
    token = create_test_token(
        user_id=str(player_c_id),
        role=Role.PLAYER,
        scopes=[Scope.MESSAGES_READ, Scope.MESSAGES_WRITE, Scope.FRIENDS_READ, Scope.FRIENDS_WRITE],
    )
    return {"Authorization": f"Bearer {token}"}


async def _create_player(db: AsyncSession, player_id: uuid.UUID, name: str) -> Player:
    player = Player(player_id=player_id, display_name=name)
    db.add(player)
    await db.flush()
    return player


async def _create_friendship(
    db: AsyncSession, player_id: uuid.UUID, friend_id: uuid.UUID
) -> None:
    friendship = Friendship(
        player_id=player_id,
        friend_id=friend_id,
        status="accepted",
    )
    db.add(friendship)
    friendship2 = Friendship(
        player_id=friend_id,
        friend_id=player_id,
        status="accepted",
    )
    db.add(friendship2)
    await db.flush()


async def _send_message(
    db: AsyncSession, sender_id: uuid.UUID, receiver_id: uuid.UUID, content: str
) -> PrivateMessage:
    msg = PrivateMessage(sender_id=sender_id, receiver_id=receiver_id, content=content)
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    return msg


# ===== 发送私聊消息 =====


class TestSendMessage:
    """发送私聊消息测试"""

    async def test_send_message_success(
        self, client: AsyncClient, player_a_headers: dict, player_a_id: uuid.UUID, player_b_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """好友之间发送私聊消息成功"""
        await _create_player(db, player_a_id, "PlayerA")
        await _create_player(db, player_b_id, "PlayerB")
        await _create_friendship(db, player_a_id, player_b_id)
        await db.commit()

        response = await client.post(
            "/api/v1/player/messages",
            json={"receiver_id": str(player_b_id), "content": "你好！"},
            headers=player_a_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["content"] == "你好！"
        assert data["data"]["sender_id"] == str(player_a_id)
        assert data["data"]["receiver_id"] == str(player_b_id)
        assert data["data"]["is_read"] is False

    async def test_send_message_not_friends(
        self, client: AsyncClient, player_a_headers: dict, player_a_id: uuid.UUID, player_c_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """非好友不能发送私聊"""
        await _create_player(db, player_a_id, "PlayerA")
        await _create_player(db, player_c_id, "PlayerC")
        await db.commit()

        response = await client.post(
            "/api/v1/player/messages",
            json={"receiver_id": str(player_c_id), "content": "你好"},
            headers=player_a_headers,
        )
        assert response.status_code == 403
        assert response.json()["code"] == "NOT_FRIENDS"

    async def test_send_message_to_self(
        self, client: AsyncClient, player_a_headers: dict, player_a_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """不能给自己发消息"""
        await _create_player(db, player_a_id, "PlayerA")
        await db.commit()

        response = await client.post(
            "/api/v1/player/messages",
            json={"receiver_id": str(player_a_id), "content": "自言自语"},
            headers=player_a_headers,
        )
        assert response.status_code == 400
        assert response.json()["code"] == "CANNOT_FRIEND_SELF"

    async def test_send_message_empty_content(
        self, client: AsyncClient, player_a_headers: dict, player_a_id: uuid.UUID, player_b_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """消息内容为空，Pydantic 校验拦截"""
        await _create_player(db, player_a_id, "PlayerA")
        await _create_player(db, player_b_id, "PlayerB")
        await _create_friendship(db, player_a_id, player_b_id)
        await db.commit()

        response = await client.post(
            "/api/v1/player/messages",
            json={"receiver_id": str(player_b_id), "content": ""},
            headers=player_a_headers,
        )
        assert response.status_code == 422

    async def test_send_message_too_long(
        self, client: AsyncClient, player_a_headers: dict, player_a_id: uuid.UUID, player_b_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """消息内容超过500字符，Pydantic 校验拦截"""
        await _create_player(db, player_a_id, "PlayerA")
        await _create_player(db, player_b_id, "PlayerB")
        await _create_friendship(db, player_a_id, player_b_id)
        await db.commit()

        response = await client.post(
            "/api/v1/player/messages",
            json={"receiver_id": str(player_b_id), "content": "a" * 501},
            headers=player_a_headers,
        )
        assert response.status_code == 422


# ===== 获取对话列表 =====


class TestGetConversations:
    """获取对话列表测试"""

    async def test_get_recent_conversations(
        self, client: AsyncClient, player_a_headers: dict, player_a_id: uuid.UUID, player_b_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """获取最近对话列表"""
        await _create_player(db, player_a_id, "PlayerA")
        await _create_player(db, player_b_id, "PlayerB")
        await _create_friendship(db, player_a_id, player_b_id)
        await _send_message(db, player_a_id, player_b_id, "第一条消息")
        await db.commit()

        response = await client.get(
            "/api/v1/player/messages/conversations",
            headers=player_a_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["conversations"]) >= 1

    async def test_get_conversation_with_friend(
        self, client: AsyncClient, player_a_headers: dict, player_a_id: uuid.UUID, player_b_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """获取与指定好友的对话历史"""
        await _create_player(db, player_a_id, "PlayerA")
        await _create_player(db, player_b_id, "PlayerB")
        await _create_friendship(db, player_a_id, player_b_id)
        await _send_message(db, player_a_id, player_b_id, "消息1")
        await _send_message(db, player_b_id, player_a_id, "消息2")
        await db.commit()

        response = await client.get(
            f"/api/v1/player/messages/conversations/{player_b_id}",
            headers=player_a_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["messages"]) >= 2


# ===== 标记消息已读 =====


class TestMarkMessageRead:
    """标记消息已读测试"""

    async def test_mark_message_read_success(
        self, client: AsyncClient, player_b_headers: dict, player_a_id: uuid.UUID, player_b_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """接收者标记消息已读成功"""
        await _create_player(db, player_a_id, "PlayerA")
        await _create_player(db, player_b_id, "PlayerB")
        await _create_friendship(db, player_a_id, player_b_id)
        msg = await _send_message(db, player_a_id, player_b_id, "你好B")
        await db.commit()

        response = await client.post(
            f"/api/v1/player/messages/{msg.message_id}/read",
            headers=player_b_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["is_read"] is True

    async def test_mark_message_not_found(
        self, client: AsyncClient, player_b_headers: dict, player_a_id: uuid.UUID, player_b_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """标记不存在的消息"""
        await _create_player(db, player_b_id, "PlayerB")
        await db.commit()

        fake_id = uuid.uuid4()
        response = await client.post(
            f"/api/v1/player/messages/{fake_id}/read",
            headers=player_b_headers,
        )
        assert response.status_code == 404
        assert response.json()["code"] == "MESSAGE_NOT_FOUND"


# ===== 未读消息 =====


class TestUnreadMessages:
    """未读消息测试"""

    async def test_get_unread_messages(
        self, client: AsyncClient, player_b_headers: dict, player_a_id: uuid.UUID, player_b_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """获取未读消息列表"""
        await _create_player(db, player_a_id, "PlayerA")
        await _create_player(db, player_b_id, "PlayerB")
        await _create_friendship(db, player_a_id, player_b_id)
        await _send_message(db, player_a_id, player_b_id, "未读消息1")
        await _send_message(db, player_a_id, player_b_id, "未读消息2")
        await db.commit()

        response = await client.get(
            "/api/v1/player/messages/unread",
            headers=player_b_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["messages"]) >= 2

    async def test_get_unread_count(
        self, client: AsyncClient, player_b_headers: dict, player_a_id: uuid.UUID, player_b_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """获取未读消息数"""
        await _create_player(db, player_a_id, "PlayerA")
        await _create_player(db, player_b_id, "PlayerB")
        await _create_friendship(db, player_a_id, player_b_id)
        await _send_message(db, player_a_id, player_b_id, "未读1")
        await _send_message(db, player_a_id, player_b_id, "未读2")
        await db.commit()

        response = await client.get(
            "/api/v1/player/messages/unread/count",
            headers=player_b_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["unread_count"] >= 2


# ===== 删除消息 =====


class TestDeleteMessage:
    """删除消息测试"""

    async def test_delete_message_success(
        self, client: AsyncClient, player_a_headers: dict, player_a_id: uuid.UUID, player_b_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """发送者可删除自己的消息"""
        await _create_player(db, player_a_id, "PlayerA")
        await _create_player(db, player_b_id, "PlayerB")
        await _create_friendship(db, player_a_id, player_b_id)
        msg = await _send_message(db, player_a_id, player_b_id, "待删除消息")
        await db.commit()

        response = await client.delete(
            f"/api/v1/player/messages/{msg.message_id}",
            headers=player_a_headers,
        )
        assert response.status_code == 200

    async def test_delete_other_message(
        self, client: AsyncClient, player_a_headers: dict, player_a_id: uuid.UUID, player_b_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """不能删除他人消息"""
        await _create_player(db, player_a_id, "PlayerA")
        await _create_player(db, player_b_id, "PlayerB")
        await _create_friendship(db, player_a_id, player_b_id)
        # B发消息给A
        msg = await _send_message(db, player_b_id, player_a_id, "B的消息")
        await db.commit()

        # A尝试删除B的消息
        response = await client.delete(
            f"/api/v1/player/messages/{msg.message_id}",
            headers=player_a_headers,
        )
        assert response.status_code == 404
        assert response.json()["code"] == "MESSAGE_NOT_FOUND"


# ===== 指标 =====


class TestMessageMetrics:
    """私聊消息指标测试"""

    async def test_metrics_exposed(self, client: AsyncClient) -> None:
        """测试指标端点暴露私聊消息指标"""
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert b"private_messages_sent_total" in response.content
        assert b"private_messages_read_total" in response.content
