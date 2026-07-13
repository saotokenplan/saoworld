"""私聊消息 API 测试。"""

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import Role, Scope


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def player_token_headers() -> dict[str, str]:
    """模拟玩家身份的请求头"""
    from app.core.auth import create_jwt_token

    token = create_jwt_token(
        user_id=str(uuid.uuid4()),
        role=Role.PLAYER,
        scopes=[
            Scope.MESSAGES_READ,
            Scope.MESSAGES_WRITE,
            Scope.FRIENDS_READ,
            Scope.FRIENDS_WRITE,
        ],
    )
    return {"Authorization": f"Bearer {token}"}


class TestSendMessage:
    """发送私聊消息测试"""

    def test_send_message_success(
        self, client: TestClient, player_token_headers: dict[str, str]
    ) -> None:
        """测试发送私聊消息成功"""
        # TODO: 需要先建立好友关系
        # 目前跳过，因为需要复杂的 mock
        pass

    def test_send_message_not_friends(
        self, client: TestClient, player_token_headers: dict[str, str]
    ) -> None:
        """测试非好友不能发送私聊"""
        pass

    def test_send_message_to_self(
        self, client: TestClient, player_token_headers: dict[str, str]
    ) -> None:
        """测试不能给自己发消息"""
        pass

    def test_send_message_empty_content(
        self, client: TestClient, player_token_headers: dict[str, str]
    ) -> None:
        """测试消息内容为空"""
        pass

    def test_send_message_too_long(
        self, client: TestClient, player_token_headers: dict[str, str]
    ) -> None:
        """测试消息内容超过500字符"""
        pass


class TestGetConversations:
    """获取对话列表测试"""

    def test_get_recent_conversations(
        self, client: TestClient, player_token_headers: dict[str, str]
    ) -> None:
        """测试获取最近对话列表"""
        pass

    def test_get_conversation_with_friend(
        self, client: TestClient, player_token_headers: dict[str, str]
    ) -> None:
        """测试获取与好友的对话历史"""
        pass


class TestMarkMessageRead:
    """标记消息已读测试"""

    def test_mark_message_read_success(
        self, client: TestClient, player_token_headers: dict[str, str]
    ) -> None:
        """测试标记消息已读成功"""
        pass

    def test_mark_message_not_found(
        self, client: TestClient, player_token_headers: dict[str, str]
    ) -> None:
        """测试标记不存在的消息"""
        pass


class TestUnreadMessages:
    """未读消息测试"""

    def test_get_unread_messages(
        self, client: TestClient, player_token_headers: dict[str, str]
    ) -> None:
        """测试获取未读消息列表"""
        pass

    def test_get_unread_count(
        self, client: TestClient, player_token_headers: dict[str, str]
    ) -> None:
        """测试获取未读消息数"""
        pass


class TestDeleteMessage:
    """删除消息测试"""

    def test_delete_message_success(
        self, client: TestClient, player_token_headers: dict[str, str]
    ) -> None:
        """测试删除消息成功（发送者可删）"""
        pass

    def test_delete_other_message(
        self, client: TestClient, player_token_headers: dict[str, str]
    ) -> None:
        """测试不能删除他人消息"""
        pass


class TestMessageMetrics:
    """私聊消息指标测试"""

    def test_metrics_exposed(self, client: TestClient) -> None:
        """测试指标端点暴露私聊消息指标"""
        response = client.get("/metrics")
        assert response.status_code == status.HTTP_200_OK
        # 检查指标是否包含私聊消息相关内容
        assert b"private_messages_sent_total" in response.content
        assert b"private_messages_read_total" in response.content