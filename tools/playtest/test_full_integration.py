import os
os.environ["VOTE_ENVIRONMENT"] = "test"
os.environ["VOTE_DATABASE_URL"] = "sqlite+aiosqlite:///file:playtest_vote.db?mode=memory&cache=shared&uri=true"
os.environ["CONTENT_ENVIRONMENT"] = "test"
os.environ["CONTENT_DATABASE_URL"] = "sqlite+aiosqlite:///file:playtest_content.db?mode=memory&cache=shared&uri=true"

import sys
import uuid
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.insert(0, '/workspace')

TEST_VOTE_DATABASE_URL = "sqlite+aiosqlite:///file:playtest_vote.db?mode=memory&cache=shared&uri=true"
TEST_CONTENT_DATABASE_URL = "sqlite+aiosqlite:///file:playtest_content.db?mode=memory&cache=shared&uri=true"

vote_test_engine = create_async_engine(TEST_VOTE_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
vote_test_session = async_sessionmaker(vote_test_engine, class_=AsyncSession, expire_on_commit=False)

content_test_engine = create_async_engine(TEST_CONTENT_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
content_test_session = async_sessionmaker(content_test_engine, class_=AsyncSession, expire_on_commit=False)


class TestVoteServiceIntegration:
    """投票服务集成测试"""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self):
        from services.vote.app.core.db import Base as VoteBase, get_db as vote_get_db

        async with vote_test_engine.begin() as conn:
            await conn.run_sync(VoteBase.metadata.create_all)

        async def override_vote_get_db() -> AsyncGenerator[AsyncSession, None]:
            async with vote_test_session() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()

        from services.vote.app.main import app as vote_app
        vote_app.dependency_overrides[vote_get_db] = override_vote_get_db

        yield

        async with vote_test_engine.begin() as conn:
            await conn.run_sync(VoteBase.metadata.drop_all)
        vote_app.dependency_overrides.clear()

    @pytest_asyncio.fixture
    async def vote_client(self) -> AsyncGenerator[AsyncClient, None]:
        from services.vote.app.main import app as vote_app
        transport = ASGITransport(app=vote_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest_asyncio.fixture
    def ops_token(self) -> str:
        from services.vote.app.core.auth import create_test_token
        from services.vote.app.schemas.auth import Role
        return create_test_token(user_id="test_ops_user", role=Role.OPS)

    @pytest_asyncio.fixture
    def player_token(self) -> str:
        from services.vote.app.core.auth import create_test_token
        from services.vote.app.schemas.auth import Role
        return create_test_token(user_id="00000000-0000-0000-0000-000000000001", role=Role.PLAYER)

    @pytest.mark.asyncio
    async def test_vote_health_endpoint(self, vote_client):
        """测试投票服务健康检查端点"""
        response = await vote_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert "data" in data

    @pytest.mark.asyncio
    async def test_vote_envelope_format(self, vote_client):
        """测试投票接口响应 envelope 格式"""
        response = await vote_client.get("/api/v1/health")
        data = response.json()
        assert "request_id" in data
        assert "data" in data
        assert data["request_id"].startswith("req_")

    @pytest.mark.asyncio
    async def test_vote_cycle_create_and_transitions(self, vote_client, ops_token):
        """测试投票周期创建与状态迁移完整流程"""
        now = datetime.now(timezone.utc)

        create_response = await vote_client.post(
            "/api/v1/ops/vote-cycles",
            json={
                "chapter_id": "chapter_01",
                "starts_at": (now - timedelta(hours=1)).isoformat(),
                "ends_at": (now + timedelta(hours=24)).isoformat(),
                "reason": "Integration test",
                "candidates": [
                    {"title": "Candidate A", "description": "Desc A", "impact_summary": "Impact A", "estimated_effort": "low"},
                    {"title": "Candidate B", "description": "Desc B", "impact_summary": "Impact B", "estimated_effort": "medium"},
                ],
            },
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        assert create_response.status_code == 201
        create_data = create_response.json()
        assert "request_id" in create_data
        assert "data" in create_data
        assert create_data["data"]["status"] == "draft"

        cycle_id = create_data["data"]["vote_cycle_id"]

        schedule_response = await vote_client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/schedule",
            json={"reason": "Schedule test"},
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        assert schedule_response.status_code == 200

        open_response = await vote_client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/open",
            json={"reason": "Open test"},
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        assert open_response.status_code == 200

    @pytest.mark.asyncio
    async def test_vote_submit_flow(self, vote_client, ops_token, player_token):
        """测试投票提交流程"""
        now = datetime.now(timezone.utc)

        create_response = await vote_client.post(
            "/api/v1/ops/vote-cycles",
            json={
                "chapter_id": "chapter_01",
                "starts_at": (now - timedelta(hours=1)).isoformat(),
                "ends_at": (now + timedelta(hours=24)).isoformat(),
                "reason": "Integration test",
                "candidates": [
                    {"title": "Candidate A", "description": "Desc A", "impact_summary": "Impact A", "estimated_effort": "low"},
                    {"title": "Candidate B", "description": "Desc B", "impact_summary": "Impact B", "estimated_effort": "medium"},
                ],
            },
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        cycle_id = create_response.json()["data"]["vote_cycle_id"]
        candidate_id = create_response.json()["data"]["candidates"][0]["candidate_id"]

        await vote_client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/schedule",
            json={"reason": "Schedule"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        await vote_client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/open",
            json={"reason": "Open"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        submit_response = await vote_client.post(
            "/api/v1/votes/submit",
            json={"candidate_id": candidate_id, "weight": 1.0},
            headers={
                "Authorization": f"Bearer {player_token}",
                "Idempotency-Key": str(uuid.uuid4()),
                "X-Trace-Id": f"trace_{uuid.uuid4().hex[:12]}",
            },
        )

        assert submit_response.status_code == 201
        submit_data = submit_response.json()
        assert "request_id" in submit_data
        assert "data" in submit_data
        assert submit_data["data"]["candidate_id"] == candidate_id

    @pytest.mark.asyncio
    async def test_vote_close_and_finalize(self, vote_client, ops_token, player_token):
        """测试投票关闭与结算流程"""
        now = datetime.now(timezone.utc)

        create_response = await vote_client.post(
            "/api/v1/ops/vote-cycles",
            json={
                "chapter_id": "chapter_01",
                "starts_at": (now - timedelta(hours=1)).isoformat(),
                "ends_at": (now + timedelta(hours=24)).isoformat(),
                "reason": "Integration test",
                "candidates": [
                    {"title": "Candidate A", "description": "Desc A", "impact_summary": "Impact A", "estimated_effort": "low"},
                    {"title": "Candidate B", "description": "Desc B", "impact_summary": "Impact B", "estimated_effort": "medium"},
                ],
            },
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        cycle_id = create_response.json()["data"]["vote_cycle_id"]
        candidate_id = create_response.json()["data"]["candidates"][0]["candidate_id"]

        await vote_client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/schedule",
            json={"reason": "Schedule"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        await vote_client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/open",
            json={"reason": "Open"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        await vote_client.post(
            "/api/v1/votes/submit",
            json={"candidate_id": candidate_id, "weight": 1.0},
            headers={
                "Authorization": f"Bearer {player_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        close_response = await vote_client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/close",
            json={"reason": "Close test"},
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        assert close_response.status_code == 200
        close_data = close_response.json()
        assert close_data["data"]["status"] == "closed"

    @pytest.mark.asyncio
    async def test_vote_history_query(self, vote_client, player_token):
        """测试投票历史查询"""
        response = await vote_client.get(
            "/api/v1/votes/history",
            headers={"Authorization": f"Bearer {player_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert "data" in data
        assert "meta" in data


class TestContentServiceIntegration:
    """内容服务集成测试"""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self):
        from services.content.app.core.db import Base as ContentBase, get_db as content_get_db

        async with content_test_engine.begin() as conn:
            await conn.run_sync(ContentBase.metadata.create_all)

        async def override_content_get_db() -> AsyncGenerator[AsyncSession, None]:
            async with content_test_session() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()

        from services.content.app.main import app as content_app
        content_app.dependency_overrides[content_get_db] = override_content_get_db

        yield

        async with content_test_engine.begin() as conn:
            await conn.run_sync(ContentBase.metadata.drop_all)
        content_app.dependency_overrides.clear()

    @pytest_asyncio.fixture
    async def content_client(self) -> AsyncGenerator[AsyncClient, None]:
        from services.content.app.main import app as content_app
        transport = ASGITransport(app=content_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest_asyncio.fixture
    def ops_token(self) -> str:
        from services.content.app.core.auth import create_test_token
        from services.content.app.schemas.auth import Role
        return create_test_token(user_id="test_ops_user", role=Role.OPS)

    @pytest_asyncio.fixture
    def player_token(self) -> str:
        from services.content.app.core.auth import create_test_token
        from services.content.app.schemas.auth import Role
        return create_test_token(user_id="00000000-0000-0000-0000-000000000001", role=Role.PLAYER)

    @pytest.mark.asyncio
    async def test_content_health_endpoint(self, content_client):
        """测试内容服务健康检查端点"""
        response = await content_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert "data" in data
        assert data["data"]["service"] == "content-service"

    @pytest.mark.asyncio
    async def test_content_envelope_format(self, content_client):
        """测试内容包接口响应 envelope 格式"""
        response = await content_client.get("/api/v1/health")
        data = response.json()
        assert "request_id" in data
        assert "data" in data
        assert data["request_id"].startswith("req_")

    @pytest.mark.asyncio
    async def test_content_package_create(self, content_client, ops_token):
        """测试内容包创建流程"""
        create_response = await content_client.post(
            "/api/v1/ops/content-packages",
            json={
                "chapter_id": "chapter_01",
                "region_id": str(uuid.uuid4()),
                "title": "Test Package",
                "summary": "Test summary",
                "package_version": "pkg_test_01",
                "payload": {"schema_version": 1, "package_type": "region"},
                "schema_version": 1,
            },
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        assert create_response.status_code == 201
        create_data = create_response.json()
        assert "request_id" in create_data
        assert "data" in create_data
        assert create_data["data"]["status"] == "packaged"

    @pytest.mark.asyncio
    async def test_content_package_release_gray(self, content_client, ops_token):
        """测试内容包灰度发布流程"""
        create_response = await content_client.post(
            "/api/v1/ops/content-packages",
            json={
                "chapter_id": "chapter_01",
                "region_id": str(uuid.uuid4()),
                "title": "Test Package",
                "summary": "Test summary",
                "package_version": "pkg_test_01",
                "payload": {"schema_version": 1, "package_type": "region"},
                "schema_version": 1,
            },
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        package_id = create_response.json()["data"]["content_package_id"]

        release_response = await content_client.post(
            f"/api/v1/ops/content-packages/{package_id}/release",
            json={
                "release_mode": "gray",
                "reason": "Gray release test",
                "gray_scope": {"player_percent": 10},
            },
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        assert release_response.status_code == 200
        release_data = release_response.json()
        assert release_data["data"]["status"] == "gray"

    @pytest.mark.asyncio
    async def test_content_package_release_full(self, content_client, ops_token):
        """测试内容包全量发布流程"""
        create_response = await content_client.post(
            "/api/v1/ops/content-packages",
            json={
                "chapter_id": "chapter_01",
                "region_id": str(uuid.uuid4()),
                "title": "Test Package",
                "summary": "Test summary",
                "package_version": "pkg_test_01",
                "payload": {"schema_version": 1, "package_type": "region"},
                "schema_version": 1,
            },
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        package_id = create_response.json()["data"]["content_package_id"]

        await content_client.post(
            f"/api/v1/ops/content-packages/{package_id}/release",
            json={"release_mode": "gray", "reason": "Gray"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        release_response = await content_client.post(
            f"/api/v1/ops/content-packages/{package_id}/release",
            json={"release_mode": "full", "reason": "Full release test"},
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        assert release_response.status_code == 200
        release_data = release_response.json()
        assert release_data["data"]["status"] == "live"

    @pytest.mark.asyncio
    async def test_content_package_rollback(self, content_client, ops_token):
        """测试内容包回滚流程"""
        create_response = await content_client.post(
            "/api/v1/ops/content-packages",
            json={
                "chapter_id": "chapter_01",
                "region_id": str(uuid.uuid4()),
                "title": "Test Package",
                "summary": "Test summary",
                "package_version": "pkg_test_01",
                "payload": {"schema_version": 1, "package_type": "region"},
                "schema_version": 1,
            },
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        package_id = create_response.json()["data"]["content_package_id"]

        await content_client.post(
            f"/api/v1/ops/content-packages/{package_id}/release",
            json={"release_mode": "gray", "reason": "Gray"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        await content_client.post(
            f"/api/v1/ops/content-packages/{package_id}/release",
            json={"release_mode": "full", "reason": "Full"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        rollback_response = await content_client.post(
            f"/api/v1/ops/content-packages/{package_id}/rollback",
            json={"target_version": "pkg_test_00", "reason": "Rollback test"},
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        assert rollback_response.status_code == 200
        rollback_data = rollback_response.json()
        assert rollback_data["data"]["status"] == "rolled_back"

    @pytest.mark.asyncio
    async def test_content_package_detail(self, content_client, ops_token, player_token):
        """测试内容包详情查询"""
        create_response = await content_client.post(
            "/api/v1/ops/content-packages",
            json={
                "chapter_id": "chapter_01",
                "region_id": str(uuid.uuid4()),
                "title": "Test Package",
                "summary": "Test summary",
                "package_version": "pkg_test_01",
                "payload": {"schema_version": 1, "package_type": "region"},
                "schema_version": 1,
            },
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        package_id = create_response.json()["data"]["content_package_id"]

        await content_client.post(
            f"/api/v1/ops/content-packages/{package_id}/release",
            json={"release_mode": "full", "reason": "Full"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        detail_response = await content_client.get(
            f"/api/v1/content/packages/{package_id}",
            headers={"Authorization": f"Bearer {player_token}"},
        )

        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        assert "request_id" in detail_data
        assert "data" in detail_data
        assert detail_data["data"]["title"] == "Test Package"


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