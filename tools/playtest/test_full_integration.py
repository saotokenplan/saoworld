import sys
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, '/workspace')


class TestVoteServiceIntegration:
    """投票服务集成测试"""

    def test_vote_health_endpoint(self):
        """测试投票服务健康检查端点"""
        with patch("services.vote.app.core.db.Base"):
            with patch("services.vote.app.core.db.engine"):
                from services.vote.app.main import app

                client = TestClient(app)
                response = client.get("/api/v1/health")

                assert response.status_code == 200
                data = response.json()
                assert "request_id" in data
                assert "data" in data

    def test_vote_envelope_format(self):
        """测试投票接口响应 envelope 格式"""
        with patch("services.vote.app.core.db.Base"):
            with patch("services.vote.app.core.db.engine"):
                from services.vote.app.main import app

                client = TestClient(app)

                response = client.get("/api/v1/health")
                data = response.json()

                assert "request_id" in data
                assert "data" in data
                assert data["request_id"].startswith("req_")


class TestContentServiceIntegration:
    """内容服务集成测试"""

    def test_content_health_endpoint(self):
        """测试内容服务健康检查端点"""
        with patch("services.content.app.core.db.Base"):
            with patch("services.content.app.core.db.engine"):
                from services.content.app.main import app

                client = TestClient(app)
                response = client.get("/api/v1/health")

                assert response.status_code == 200
                data = response.json()
                assert "request_id" in data
                assert "data" in data
                assert data["data"]["service"] == "content-service"

    def test_content_envelope_format(self):
        """测试内容包接口响应 envelope 格式"""
        with patch("services.content.app.core.db.Base"):
            with patch("services.content.app.core.db.engine"):
                from services.content.app.main import app

                client = TestClient(app)

                response = client.get("/api/v1/health")
                data = response.json()

                assert "request_id" in data
                assert "data" in data
                assert data["request_id"].startswith("req_")


class TestEventBusIntegration:
    """事件总线集成测试"""

    @pytest.mark.asyncio
    async def test_event_bus_publish(self):
        """测试事件总线发布机制"""
        from workers.events.event_bus import EventBus
        from workers.events.schemas import EventType

        mock_redis = MagicMock()
        mock_redis.publish = AsyncMock(return_value=1)

        event_bus = EventBus()
        event_bus._redis = mock_redis

        await event_bus.publish(
            event_type=EventType.VOTE_RESULT_FINALIZED,
            payload={
                "cycle_id": str(uuid.uuid4()),
                "winning_candidate_id": str(uuid.uuid4()),
                "total_votes": 100,
            },
            trace_id="trace_test",
        )

        mock_redis.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_event_bus_subscribe(self):
        """测试事件总线订阅机制"""
        from workers.events.event_bus import EventBus
        from workers.events.schemas import EventType

        mock_redis = MagicMock()
        mock_pubsub = MagicMock()
        mock_redis.pubsub = MagicMock(return_value=mock_pubsub)
        mock_pubsub.subscribe = AsyncMock()

        event_bus = EventBus()
        event_bus._redis = mock_redis

        await event_bus.subscribe([EventType.VOTE_RESULT_FINALIZED, EventType.CONTENT_PACKAGE_RELEASED])

        mock_redis.pubsub.assert_called_once()
        mock_pubsub.subscribe.assert_called_once()