import os
import sys

os.environ["CONTENT_ENVIRONMENT"] = "test"
os.environ["CONTENT_DATABASE_URL"] = "sqlite+aiosqlite:///file:playtest_content.db?mode=memory&cache=shared&uri=true"

import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_CONTENT_DATABASE_URL = "sqlite+aiosqlite:///file:playtest_content.db?mode=memory&cache=shared&uri=true"

content_test_engine = create_async_engine(TEST_CONTENT_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
content_test_session = async_sessionmaker(content_test_engine, class_=AsyncSession, expire_on_commit=False)


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


class TestContentServiceIntegration:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self):
        old_path = sys.path.copy()
        _clean_app_modules()
        sys.path.insert(0, '/workspace/services/content')

        try:
            from app.core.db import Base as ContentBase, get_db as content_get_db

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

            from app.main import app as content_app
            content_app.dependency_overrides[content_get_db] = override_content_get_db

            yield

            async with content_test_engine.begin() as conn:
                await conn.run_sync(ContentBase.metadata.drop_all)
            content_app.dependency_overrides.clear()
        finally:
            sys.path[:] = old_path
            _clean_app_modules()

    @pytest.fixture
    def content_client(self):
        old_path = sys.path.copy()
        _clean_app_modules()
        sys.path.insert(0, '/workspace/services/content')

        try:
            from app.main import app as content_app
            with TestClient(content_app) as client:
                yield client
        finally:
            sys.path[:] = old_path
            _clean_app_modules()

    @pytest.fixture
    def ops_token(self) -> str:
        old_path = sys.path.copy()
        _clean_app_modules()
        sys.path.insert(0, '/workspace/services/content')

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
        sys.path.insert(0, '/workspace/services/content')

        try:
            from app.core.auth import create_test_token
            from app.schemas.auth import Role
            token: str = create_test_token(user_id="00000000-0000-0000-0000-000000000001", role=Role.PLAYER)
            return token
        finally:
            sys.path[:] = old_path
            _clean_app_modules()

    def test_content_health_endpoint(self, content_client):
        response = content_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert "data" in data

    def test_content_envelope_format(self, content_client):
        response = content_client.get("/api/v1/health")
        data = response.json()
        assert "request_id" in data
        assert "data" in data
        assert data["request_id"].startswith("req_")

    def test_content_package_create(self, content_client, ops_token):
        create_response = content_client.post(
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

    def test_content_package_release_gray(self, content_client, ops_token):
        create_response = content_client.post(
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

        release_response = content_client.post(
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

    def test_content_package_release_full(self, content_client, ops_token):
        create_response = content_client.post(
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

        content_client.post(
            f"/api/v1/ops/content-packages/{package_id}/release",
            json={"release_mode": "gray", "reason": "Gray"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        release_response = content_client.post(
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

    def test_content_package_rollback(self, content_client, ops_token):
        create_response = content_client.post(
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

        content_client.post(
            f"/api/v1/ops/content-packages/{package_id}/release",
            json={"release_mode": "gray", "reason": "Gray"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        content_client.post(
            f"/api/v1/ops/content-packages/{package_id}/release",
            json={"release_mode": "full", "reason": "Full"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        rollback_response = content_client.post(
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

    def test_content_package_detail(self, content_client, ops_token, player_token):
        create_response = content_client.post(
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

        content_client.post(
            f"/api/v1/ops/content-packages/{package_id}/release",
            json={"release_mode": "gray", "reason": "Gray"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        content_client.post(
            f"/api/v1/ops/content-packages/{package_id}/release",
            json={"release_mode": "full", "reason": "Full"},
            headers={"Authorization": f"Bearer {ops_token}", "Idempotency-Key": str(uuid.uuid4())},
        )

        detail_response = content_client.get(
            f"/api/v1/content/packages/{package_id}",
            headers={"Authorization": f"Bearer {player_token}"},
        )

        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        assert "request_id" in detail_data
        assert "data" in detail_data
        assert detail_data["data"]["title"] == "Test Package"