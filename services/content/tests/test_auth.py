import pytest
from httpx import AsyncClient

from app.core.auth import (
    ExpiredTokenError,
    InvalidTokenError,
    MissingTokenError,
    create_test_token,
)
from app.schemas.auth import Role


@pytest.mark.asyncio
async def test_no_token_returns_401(client: AsyncClient):
    response = await client.get("/api/v1/content/updates")
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == MissingTokenError().code


@pytest.mark.asyncio
async def test_invalid_token_returns_401(client: AsyncClient):
    response = await client.get(
        "/api/v1/content/updates",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == InvalidTokenError().code


@pytest.mark.asyncio
async def test_malformed_token_returns_401(client: AsyncClient):
    response = await client.get(
        "/api/v1/content/updates",
        headers={"Authorization": "NotBearer token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_expired_token_returns_401(client: AsyncClient):
    expired_token = create_test_token(
        user_id="test_user",
        role=Role.PLAYER,
        expire_minutes=-1,
    )
    response = await client.get(
        "/api/v1/content/updates",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == ExpiredTokenError().code


@pytest.mark.asyncio
async def test_wrong_scope_returns_403(client: AsyncClient):
    token = create_test_token(
        user_id="test_user",
        role=Role.PLAYER,
        scopes=["votes:read"],
    )
    response = await client.get(
        "/api/v1/content/updates",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    data = response.json()
    assert data["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_player_cannot_access_ops_endpoints(
    client: AsyncClient, player_token: str
):
    response = await client.post(
        "/api/v1/ops/content-packages",
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "test-auth-001",
        },
        json={
            "chapter_id": "chapter_01",
            "package_version": "pkg_test_001",
            "title": "测试内容包",
            "payload": {"test": "data"},
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_ops_can_access_ops_endpoints(
    client: AsyncClient, ops_token: str
):
    response = await client.post(
        "/api/v1/ops/content-packages",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-auth-002",
        },
        json={
            "chapter_id": "chapter_01",
            "package_version": "pkg_test_002",
            "title": "测试内容包",
            "payload": {"test": "data"},
        },
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_content_read_scope_works(client: AsyncClient, content_packages):
    token = create_test_token(
        user_id="test_user",
        role=Role.PLAYER,
        scopes=["content:read"],
    )
    response = await client.get(
        "/api/v1/content/updates",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_auth_error_envelope_format(client: AsyncClient):
    response = await client.get("/api/v1/content/updates")
    data = response.json()
    assert "code" in data
    assert "message" in data
    assert "request_id" in data
