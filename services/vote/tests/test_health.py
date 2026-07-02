import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get(f"{settings.api_v1_prefix}/health")
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert data["data"]["service"] == settings.app_name
    assert data["data"]["version"] == settings.app_version
    assert data["data"]["status"] == "ok"


@pytest.mark.asyncio
async def test_get_current_vote_no_open_cycle(client: AsyncClient, player_token: str):
    response = await client.get(
        f"{settings.api_v1_prefix}/votes/current",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "NO_OPEN_VOTE_CYCLE"
    assert "request_id" in data
