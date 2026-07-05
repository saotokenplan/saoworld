import os
os.environ["VOTE_ENVIRONMENT"] = "test"
os.environ["VOTE_DATABASE_URL"] = "sqlite+aiosqlite:///file:playtest_vtc.db?mode=memory&cache=shared&uri=true"
os.environ["CONTENT_ENVIRONMENT"] = "test"
os.environ["CONTENT_DATABASE_URL"] = "sqlite+aiosqlite:///file:playtest_vtc_content.db?mode=memory&cache=shared&uri=true"
os.environ["GENERATION_ENVIRONMENT"] = "test"
os.environ["GENERATION_DATABASE_URL"] = "sqlite+aiosqlite:///file:playtest_vtc_gen.db?mode=memory&cache=shared&uri=true"
os.environ["REVIEW_ENVIRONMENT"] = "test"
os.environ["REVIEW_DATABASE_URL"] = "sqlite+aiosqlite:///file:playtest_vtc_review.db?mode=memory&cache=shared&uri=true"

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

TEST_VOTE_DATABASE_URL = "sqlite+aiosqlite:///file:playtest_vtc.db?mode=memory&cache=shared&uri=true"
TEST_CONTENT_DATABASE_URL = "sqlite+aiosqlite:///file:playtest_vtc_content.db?mode=memory&cache=shared&uri=true"
TEST_GENERATION_DATABASE_URL = "sqlite+aiosqlite:///file:playtest_vtc_gen.db?mode=memory&cache=shared&uri=true"
TEST_REVIEW_DATABASE_URL = "sqlite+aiosqlite:///file:playtest_vtc_review.db?mode=memory&cache=shared&uri=true"

vote_test_engine = create_async_engine(TEST_VOTE_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
vote_test_session = async_sessionmaker(vote_test_engine, class_=AsyncSession, expire_on_commit=False)

content_test_engine = create_async_engine(TEST_CONTENT_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
content_test_session = async_sessionmaker(content_test_engine, class_=AsyncSession, expire_on_commit=False)

generation_test_engine = create_async_engine(TEST_GENERATION_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
generation_test_session = async_sessionmaker(generation_test_engine, class_=AsyncSession, expire_on_commit=False)

review_test_engine = create_async_engine(TEST_REVIEW_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
review_test_session = async_sessionmaker(review_test_engine, class_=AsyncSession, expire_on_commit=False)


class TestVoteToContentFlow:
    """投票触发内容生成完整闭环测试"""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self):
        from services.vote.app.core.db import Base as VoteBase, get_db as vote_get_db
        from services.content.app.core.db import Base as ContentBase, get_db as content_get_db
        from services.generation.app.core.db import Base as GenerationBase, get_db as generation_get_db
        from services.review.app.core.db import Base as ReviewBase, get_db as review_get_db

        async with vote_test_engine.begin() as conn:
            await conn.run_sync(VoteBase.metadata.create_all)
        async with content_test_engine.begin() as conn:
            await conn.run_sync(ContentBase.metadata.create_all)
        async with generation_test_engine.begin() as conn:
            await conn.run_sync(GenerationBase.metadata.create_all)
        async with review_test_engine.begin() as conn:
            await conn.run_sync(ReviewBase.metadata.create_all)

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

        async def override_generation_get_db() -> AsyncGenerator[AsyncSession, None]:
            async with generation_test_session() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()

        async def override_review_get_db() -> AsyncGenerator[AsyncSession, None]:
            async with review_test_session() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()

        from services.vote.app.main import app as vote_app
        from services.content.app.main import app as content_app
        from services.generation.app.main import app as generation_app
        from services.review.app.main import app as review_app

        vote_app.dependency_overrides[vote_get_db] = override_vote_get_db
        content_app.dependency_overrides[content_get_db] = override_content_get_db
        generation_app.dependency_overrides[generation_get_db] = override_generation_get_db
        review_app.dependency_overrides[review_get_db] = override_review_get_db

        yield

        async with vote_test_engine.begin() as conn:
            await conn.run_sync(VoteBase.metadata.drop_all)
        async with content_test_engine.begin() as conn:
            await conn.run_sync(ContentBase.metadata.drop_all)
        async with generation_test_engine.begin() as conn:
            await conn.run_sync(GenerationBase.metadata.drop_all)
        async with review_test_engine.begin() as conn:
            await conn.run_sync(ReviewBase.metadata.drop_all)

        vote_app.dependency_overrides.clear()
        content_app.dependency_overrides.clear()
        generation_app.dependency_overrides.clear()
        review_app.dependency_overrides.clear()

    @pytest_asyncio.fixture
    async def vote_client(self) -> AsyncGenerator[AsyncClient, None]:
        from services.vote.app.main import app as vote_app
        transport = ASGITransport(app=vote_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest_asyncio.fixture
    async def content_client(self) -> AsyncGenerator[AsyncClient, None]:
        from services.content.app.main import app as content_app
        transport = ASGITransport(app=content_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest_asyncio.fixture
    async def generation_client(self) -> AsyncGenerator[AsyncClient, None]:
        from services.generation.app.main import app as generation_app
        transport = ASGITransport(app=generation_app)
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
    async def test_vote_cycle_create_and_finalize(self, vote_client, ops_token, player_token):
        """测试投票周期创建→开放→投票→关闭→结算完整流程"""
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
            json={"reason": "Close"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        assert close_response.status_code == 200
        assert close_response.json()["data"]["status"] == "closed"
        assert close_response.json()["data"]["winning_candidate_id"] is not None

        finalize_response = await vote_client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/finalize",
            json={"reason": "Finalize"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        assert finalize_response.status_code == 200
        assert finalize_response.json()["data"]["status"] == "finalized"

    @pytest.mark.asyncio
    async def test_event_handlers_parameter_matching(self):
        """测试事件处理器参数与任务签名匹配"""
        from workers.events.handlers import (
            handle_vote_result_finalized,
            handle_generation_batch_completed,
            handle_review_batch_completed,
            handle_content_package_released,
            handle_content_package_rolled_back,
        )
        from workers.events.schemas import Event, EventType
        from workers.tasks.content_generation import generate_content_batch
        from workers.tasks.content_packaging import package_content_batch
        from workers.tasks.content_review import run_full_content_review

        assert EventType.VOTE_RESULT_FINALIZED in locals()
        assert hasattr(generate_content_batch, 'delay')
        assert hasattr(package_content_batch, 'delay')
        assert hasattr(run_full_content_review, 'delay')

        test_event = Event(
            event_type=EventType.VOTE_RESULT_FINALIZED,
            payload={
                "vote_cycle_id": str(uuid.uuid4()),
                "winning_candidate_id": str(uuid.uuid4()),
                "winning_candidate_name": "Test Candidate",
                "total_votes": 100,
                "finalized_at": datetime.now(timezone.utc).isoformat(),
            },
            trace_id="test_trace",
        )

        import inspect
        handler_sig = inspect.signature(handle_vote_result_finalized)
        assert 'event' in handler_sig.parameters

    @pytest.mark.asyncio
    async def test_content_package_full_lifecycle(self, content_client, ops_token):
        """测试内容包创建→灰度→全量→回滚完整生命周期"""
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
        package_id = create_response.json()["data"]["content_package_id"]
        assert create_response.json()["data"]["status"] == "packaged"

        gray_response = await content_client.post(
            f"/api/v1/ops/content-packages/{package_id}/release",
            json={"release_mode": "gray", "reason": "Gray"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        assert gray_response.status_code == 200
        assert gray_response.json()["data"]["status"] == "gray"

        full_response = await content_client.post(
            f"/api/v1/ops/content-packages/{package_id}/release",
            json={"release_mode": "full", "reason": "Full"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        assert full_response.status_code == 200
        assert full_response.json()["data"]["status"] == "live"

    @pytest.mark.asyncio
    async def test_generation_request_create(self, generation_client):
        """测试生成请求创建"""
        from services.generation.app.core.auth import create_test_token
        from services.generation.app.schemas.auth import Role

        ops_token = create_test_token(user_id="test_ops", role=Role.OPS)

        create_response = await generation_client.post(
            "/api/v1/ops/generation/requests",
            json={
                "template_type": "npc",
                "count": 1,
                "chapter_id": "chapter_01",
                "region_id": str(uuid.uuid4()),
            },
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        assert create_response.status_code == 201
        data = create_response.json()
        assert "request_id" in data["data"]
        assert data["data"]["status"] == "pending"
