import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
async def test_player_endpoint_requires_auth(client: AsyncClient):
    response = await client.get(f"{settings.api_v1_prefix}/player/info")
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "MISSING_TOKEN"


@pytest.mark.asyncio
async def test_ops_endpoint_requires_auth(client: AsyncClient):
    response = await client.get(f"{settings.api_v1_prefix}/ops/players")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token(client: AsyncClient):
    response = await client.get(
        f"{settings.api_v1_prefix}/player/info",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_player_cannot_access_ops_endpoint(client: AsyncClient, player_token: str):
    response = await client.get(
        f"{settings.api_v1_prefix}/ops/players",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 403
    data = response.json()
    assert data["code"] == "FORBIDDEN"