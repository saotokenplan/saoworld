import pytest
from httpx import AsyncClient

from app.core.auth import create_test_token
from app.schemas.auth import Role


@pytest.mark.asyncio
async def test_no_token_returns_401(client: AsyncClient):
    response = await client.get("/api/v1/ops/review/records")
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "MISSING_TOKEN"


@pytest.mark.asyncio
async def test_invalid_token_returns_401(client: AsyncClient):
    response = await client.get(
        "/api/v1/ops/review/records",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_malformed_token_returns_401(client: AsyncClient):
    response = await client.get(
        "/api/v1/ops/review/records",
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
        "/api/v1/ops/review/records",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "TOKEN_EXPIRED"


@pytest.mark.asyncio
async def test_player_cannot_access_ops_endpoints(
    client: AsyncClient, player_token: str
):
    response = await client.get(
        "/api/v1/ops/review/records",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_ops_can_access_ops_endpoints(
    client: AsyncClient, ops_token: str
):
    response = await client.get(
        "/api/v1/ops/review/records",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_reviewer_can_access_review_endpoints(
    client: AsyncClient, reviewer_token: str, review_records
):
    review = review_records[0]
    response = await client.post(
        f"/api/v1/ops/review/records/{review.review_id}/result",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "test-reviewer-update-001",
        },
        json={"result": "approved"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_ops_can_access_review_endpoints(
    client: AsyncClient, ops_token: str, review_records
):
    review = review_records[0]
    response = await client.post(
        f"/api/v1/ops/review/records/{review.review_id}/result",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-ops-update-001",
        },
        json={"result": "approved"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_auth_error_envelope_format(client: AsyncClient):
    response = await client.get("/api/v1/ops/review/records")
    data = response.json()
    assert "code" in data
    assert "message" in data
    assert "request_id" in data
