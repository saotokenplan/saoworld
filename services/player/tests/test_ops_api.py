import uuid

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.core.errors import PlayerErrorCodes


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
    assert data["code"] == PlayerErrorCodes.PLAYER_NOT_FOUND


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


@pytest.mark.asyncio
async def test_unlock_region_player_not_found(client: AsyncClient, ops_token: str):
    fake_id = uuid.uuid4()
    response = await client.post(
        f"{settings.api_v1_prefix}/ops/players/{fake_id}/regions/region_forest_01/unlock",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-unlock-region-not-found",
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.PLAYER_NOT_FOUND


@pytest.mark.asyncio
async def test_list_players_pagination(client: AsyncClient, ops_token: str, test_player):
    response = await client.get(
        f"{settings.api_v1_prefix}/ops/players?limit=10&offset=0",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["limit"] == 10
    assert data["meta"]["offset"] == 0
    assert data["meta"]["total"] >= 1


@pytest.mark.asyncio
async def test_create_player_with_chapter(client: AsyncClient, ops_token: str):
    response = await client.post(
        f"{settings.api_v1_prefix}/ops/players",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-player-chapter",
        },
        json={"display_name": "ChapterPlayer", "chapter_id": "ch_chapter_02"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["display_name"] == "ChapterPlayer"
    assert data["data"]["chapter_id"] == "ch_chapter_02"


@pytest.mark.asyncio
async def test_update_player_chapter_id(client: AsyncClient, ops_token: str, test_player):
    response = await client.put(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-update-player-chapter",
        },
        json={"chapter_id": "ch_chapter_02"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["chapter_id"] == "ch_chapter_02"


@pytest.mark.asyncio
async def test_update_player_empty_display_name(client: AsyncClient, ops_token: str, test_player):
    response = await client.put(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-update-player-empty-name",
        },
        json={"display_name": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ops_get_player_quests_success(client: AsyncClient, ops_token: str, test_player, test_player_quest):
    response = await client.get(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}/quests",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert "meta" in data
    assert len(data["data"]) == 1
    assert data["data"][0]["quest_id"] == "quest_rescue_01"


@pytest.mark.asyncio
async def test_ops_get_player_quests_player_not_found(client: AsyncClient, ops_token: str):
    fake_id = uuid.uuid4()
    response = await client.get(
        f"{settings.api_v1_prefix}/ops/players/{fake_id}/quests",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.PLAYER_NOT_FOUND


@pytest.mark.asyncio
async def test_ops_create_player_quest_success(client: AsyncClient, ops_token: str, test_player):
    response = await client.post(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}/quests",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-player-quest-001",
        },
        json={
            "quest_id": "quest_new_01",
            "status": "available",
            "objectives_jsonb": {"obj1": "找到宝藏"},
            "rewards_jsonb": {"gold": 500},
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "request_id" in data
    assert data["data"]["quest_id"] == "quest_new_01"
    assert data["data"]["status"] == "available"


@pytest.mark.asyncio
async def test_ops_create_player_quest_already_exists(client: AsyncClient, ops_token: str, test_player, test_player_quest):
    response = await client.post(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}/quests",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-player-quest-duplicate",
        },
        json={"quest_id": "quest_rescue_01", "status": "available"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == PlayerErrorCodes.QUEST_ALREADY_ACCEPTED


@pytest.mark.asyncio
async def test_ops_update_quest_status_success(client: AsyncClient, ops_token: str, test_player, test_player_quest):
    response = await client.patch(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}/quests/quest_rescue_01/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-update-quest-status-001",
        },
        json={"status": "completed"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["quest_id"] == "quest_rescue_01"
    assert data["data"]["status"] == "completed"


@pytest.mark.asyncio
async def test_ops_update_quest_status_invalid_transition(client: AsyncClient, ops_token: str, test_player):
    import uuid as uuid_module
    from app.domain.models import PlayerQuest
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        completed_quest = PlayerQuest(
            player_quest_id=uuid_module.uuid4(),
            player_id=test_player.player_id,
            quest_id="quest_done_01",
            status="completed",
            objectives_jsonb={},
            rewards_jsonb={},
        )
        session.add(completed_quest)
        await session.commit()

    response = await client.patch(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}/quests/quest_done_01/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-update-quest-status-invalid",
        },
        json={"status": "active"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == PlayerErrorCodes.QUEST_INVALID_STATE_TRANSITION