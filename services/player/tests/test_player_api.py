import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.core.errors import PlayerErrorCodes


@pytest.mark.asyncio
async def test_get_player_info_success(client: AsyncClient, player_token: str, test_player):
    response = await client.get(
        f"{settings.api_v1_prefix}/player/info",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert data["data"]["display_name"] == "TestPlayer"
    assert data["data"]["chapter_id"] == "ch_prologue_01"


@pytest.mark.asyncio
async def test_get_player_info_not_found(client: AsyncClient, player_token: str):
    response = await client.get(
        f"{settings.api_v1_prefix}/player/info",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.PLAYER_NOT_FOUND


@pytest.mark.asyncio
async def test_get_player_info_unauthorized(client: AsyncClient):
    response = await client.get(f"{settings.api_v1_prefix}/player/info")
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "MISSING_TOKEN"


@pytest.mark.asyncio
async def test_get_player_quests_success(client: AsyncClient, player_token: str, test_player, test_player_quest):
    response = await client.get(
        f"{settings.api_v1_prefix}/player/quests",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert len(data["data"]) == 1
    assert data["data"][0]["quest_id"] == "quest_rescue_01"
    assert data["data"][0]["status"] == "active"
    assert "meta" in data
    assert data["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_get_player_quests_filter_status(client: AsyncClient, player_token: str, test_player, test_player_quest):
    response = await client.get(
        f"{settings.api_v1_prefix}/player/quests?status=active",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1


@pytest.mark.asyncio
async def test_get_player_quests_invalid_status(client: AsyncClient, player_token: str, test_player):
    response = await client.get(
        f"{settings.api_v1_prefix}/player/quests?status=invalid",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == PlayerErrorCodes.INVALID_QUEST_STATUS


@pytest.mark.asyncio
async def test_get_player_regions_success(client: AsyncClient, player_token: str, test_player, test_player_region):
    response = await client.get(
        f"{settings.api_v1_prefix}/player/regions",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert len(data["data"]) == 1
    assert data["data"][0]["region_id"] == "region_wasteland_01"
    assert data["data"][0]["reputation"] == 50


@pytest.mark.asyncio
async def test_get_player_quests_pagination(client: AsyncClient, player_token: str, test_player, test_player_quest):
    response = await client.get(
        f"{settings.api_v1_prefix}/player/quests?limit=1&offset=0",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "meta" in data
    assert data["meta"]["limit"] == 1
    assert data["meta"]["offset"] == 0
    assert data["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_get_player_quests_empty(client: AsyncClient, player_token: str, test_player):
    response = await client.get(
        f"{settings.api_v1_prefix}/player/quests",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 0
    assert data["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_get_player_regions_pagination(client: AsyncClient, player_token: str, test_player, test_player_region):
    response = await client.get(
        f"{settings.api_v1_prefix}/player/regions?limit=10&offset=0",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "meta" in data
    assert data["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_get_player_regions_empty(client: AsyncClient, player_token: str, test_player):
    response = await client.get(
        f"{settings.api_v1_prefix}/player/regions",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 0
    assert data["meta"]["total"] == 0