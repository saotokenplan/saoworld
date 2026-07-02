import uuid

import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
async def test_create_player_success(client: AsyncClient, ops_token: str):
    response = await client.post(
        f"{settings.api_v1_prefix}/ops/players",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-player-001",
        },
        json={"display_name": "NewPlayer", "chapter_id": "ch_prologue_01"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert data["data"]["display_name"] == "NewPlayer"
    assert data["data"]["chapter_id"] == "ch_prologue_01"


@pytest.mark.asyncio
async def test_create_player_validation(client: AsyncClient, ops_token: str):
    response = await client.post(
        f"{settings.api_v1_prefix}/ops/players",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-player-002",
        },
        json={"display_name": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_players_success(client: AsyncClient, ops_token: str, test_player):
    response = await client.get(
        f"{settings.api_v1_prefix}/ops/players",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert "meta" in data


@pytest.mark.asyncio
async def test_get_player_detail_success(client: AsyncClient, ops_token: str, test_player):
    response = await client.get(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["data"]["display_name"] == "TestPlayer"


@pytest.mark.asyncio
async def test_get_player_detail_not_found(client: AsyncClient, ops_token: str):
    fake_id = uuid.uuid4()
    response = await client.get(
        f"{settings.api_v1_prefix}/ops/players/{fake_id}",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "PLAYER_NOT_FOUND"


@pytest.mark.asyncio
async def test_update_player_success(client: AsyncClient, ops_token: str, test_player):
    response = await client.put(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-update-player-001",
        },
        json={"display_name": "UpdatedPlayer"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["data"]["display_name"] == "UpdatedPlayer"


@pytest.mark.asyncio
async def test_update_player_not_found(client: AsyncClient, ops_token: str):
    fake_id = uuid.uuid4()
    response = await client.put(
        f"{settings.api_v1_prefix}/ops/players/{fake_id}",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-update-player-002",
        },
        json={"display_name": "UpdatedPlayer"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_unlock_region_success(client: AsyncClient, ops_token: str, test_player):
    response = await client.post(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}/regions/region_forest_01/unlock",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-unlock-region-001",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["data"]["region_id"] == "region_forest_01"
    assert data["data"]["unlocked_at"] is not None