import os
import sys

os.environ["VOTE_ENVIRONMENT"] = "test"
os.environ["VOTE_DATABASE_URL"] = "sqlite+aiosqlite:///file:playtest_vote.db?mode=memory&cache=shared&uri=true"

import uuid
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_VOTE_DATABASE_URL = "sqlite+aiosqlite:///file:playtest_vote.db?mode=memory&cache=shared&uri=true"

vote_test_engine = create_async_engine(TEST_VOTE_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
vote_test_session = async_sessionmaker(vote_test_engine, class_=AsyncSession, expire_on_commit=False)


def _clean_app_modules():
    modules_to_remove = [key for key in sys.modules.keys() if key.startswith('app')]
    for mod in modules_to_remove:
        del sys.modules[mod]

    try:
        from prometheus_client import REGISTRY
        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            try:
                REGISTRY.unregister(collector)
            except Exception:
                pass
    except Exception:
        pass


class TestVoteServiceIntegration:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self):
        old_path = sys.path.copy()
        _clean_app_modules()
        sys.path.insert(0, '/workspace/services/vote')

        try:
            from app.core.db import Base as VoteBase, get_db as vote_get_db

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

            from app.main import app as vote_app
            vote_app.dependency_overrides[vote_get_db] = override_vote_get_db

            yield

            async with vote_test_engine.begin() as conn:
                await conn.run_sync(VoteBase.metadata.drop_all)
            vote_app.dependency_overrides.clear()
        finally:
            sys.path[:] = old_path
            _clean_app_modules()

    @pytest.fixture
    def vote_client(self):
        from unittest.mock import AsyncMock, patch

        old_path = sys.path.copy()
        _clean_app_modules()
        sys.path.insert(0, '/workspace/services/vote')

        try:
            from app.main import app as vote_app

            mock_get_contribution = AsyncMock(return_value=1000)
            mock_close = AsyncMock()

            with patch("app.core.player_client.PlayerContributionClient.get_contribution", mock_get_contribution), \
                 patch("app.core.player_client.PlayerContributionClient.close", mock_close):
                with TestClient(vote_app) as client:
                    yield client
        finally:
            sys.path[:] = old_path
            _clean_app_modules()

    @pytest.fixture
    def ops_token(self) -> str:
        old_path = sys.path.copy()
        _clean_app_modules()
        sys.path.insert(0, '/workspace/services/vote')

        try:
            from app.core.auth import create_test_token
            from app.schemas.auth import Role
            token: str = create_test_token(user_id="test_ops_user", role=Role.OPS)
            return token
        finally:
            sys.path[:] = old_path
            _clean_app_modules()

    @pytest.fixture
    def player_token(self) -> str:
        old_path = sys.path.copy()
        _clean_app_modules()
        sys.path.insert(0, '/workspace/services/vote')

        try:
            from app.core.auth import create_test_token
            from app.schemas.auth import Role
            token: str = create_test_token(user_id="00000000-0000-0000-0000-000000000001", role=Role.PLAYER)
            return token
        finally:
            sys.path[:] = old_path
            _clean_app_modules()

    def test_vote_health_endpoint(self, vote_client):
        response = vote_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert "data" in data

    def test_vote_envelope_format(self, vote_client):
        response = vote_client.get("/api/v1/health")
        data = response.json()
        assert "request_id" in data
        assert "data" in data
        assert data["request_id"].startswith("req_")

    def test_vote_cycle_create_and_transitions(self, vote_client, ops_token):
        now = datetime.now(timezone.utc)

        create_response = vote_client.post(
            "/api/v1/ops/vote-cycles",
            json={
                "chapter_id": "chapter_01",
                "starts_at": (now - timedelta(hours=1)).isoformat(),
                "ends_at": (now + timedelta(hours=24)).isoformat(),
                "reason": "Integration test",
                "candidates": [
                    {"title": "Candidate A", "summary": "Summary A", "description": "Desc A"},
                    {"title": "Candidate B", "summary": "Summary B", "description": "Desc B"},
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

        schedule_response = vote_client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/schedule",
            json={"reason": "Schedule test"},
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        assert schedule_response.status_code == 200

        open_response = vote_client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/open",
            json={"reason": "Open test"},
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        assert open_response.status_code == 200

    def test_vote_submit_flow(self, vote_client, ops_token, player_token):
        now = datetime.now(timezone.utc)

        create_response = vote_client.post(
            "/api/v1/ops/vote-cycles",
            json={
                "chapter_id": "chapter_01",
                "starts_at": (now - timedelta(hours=1)).isoformat(),
                "ends_at": (now + timedelta(hours=24)).isoformat(),
                "reason": "Integration test",
                "candidates": [
                    {"title": "Candidate A", "summary": "Summary A", "description": "Desc A"},
                    {"title": "Candidate B", "summary": "Summary B", "description": "Desc B"},
                ],
            },
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        cycle_id = create_response.json()["data"]["vote_cycle_id"]
        candidate_id = create_response.json()["data"]["candidates"][0]["candidate_id"]

        vote_client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/schedule",
            json={"reason": "Schedule"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        vote_client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/open",
            json={"reason": "Open"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        submit_response = vote_client.post(
            "/api/v1/votes/submit",
            json={"candidate_id": candidate_id, "weight": 1.0, "device_fingerprint_hash": "test_fingerprint"},
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

    def test_vote_close_and_finalize(self, vote_client, ops_token, player_token):
        now = datetime.now(timezone.utc)

        create_response = vote_client.post(
            "/api/v1/ops/vote-cycles",
            json={
                "chapter_id": "chapter_01",
                "starts_at": (now - timedelta(hours=1)).isoformat(),
                "ends_at": (now + timedelta(hours=24)).isoformat(),
                "reason": "Integration test",
                "candidates": [
                    {"title": "Candidate A", "summary": "Summary A", "description": "Desc A"},
                    {"title": "Candidate B", "summary": "Summary B", "description": "Desc B"},
                ],
            },
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        cycle_id = create_response.json()["data"]["vote_cycle_id"]
        candidate_id = create_response.json()["data"]["candidates"][0]["candidate_id"]

        vote_client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/schedule",
            json={"reason": "Schedule"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        vote_client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/open",
            json={"reason": "Open"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        vote_client.post(
            "/api/v1/votes/submit",
            json={"candidate_id": candidate_id, "weight": 1.0, "device_fingerprint_hash": "test_fingerprint"},
            headers={
                "Authorization": f"Bearer {player_token}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )

        close_response = vote_client.post(
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

    def test_vote_history_query(self, vote_client, player_token):
        response = vote_client.get(
            "/api/v1/votes/history",
            headers={"Authorization": f"Bearer {player_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert "data" in data
        assert "meta" in data
