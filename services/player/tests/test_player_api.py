import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.core.errors import PlayerErrorCodes
from tests.conftest import TestSessionLocal


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


@pytest.mark.asyncio
async def test_get_player_quest_detail_success(client: AsyncClient, player_token: str, test_player, test_player_quest):
    response = await client.get(
        f"{settings.api_v1_prefix}/player/quests/quest_rescue_01",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert data["data"]["quest_id"] == "quest_rescue_01"
    assert data["data"]["status"] == "active"


@pytest.mark.asyncio
async def test_get_player_quest_detail_not_found(client: AsyncClient, player_token: str, test_player):
    response = await client.get(
        f"{settings.api_v1_prefix}/player/quests/quest_nonexistent_01",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.QUEST_NOT_FOUND


@pytest.mark.asyncio
async def test_accept_quest_success(client: AsyncClient, player_token: str, test_player):
    async with TestSessionLocal() as session:
        from app.domain.models import PlayerQuest
        import uuid

        initial_quest = PlayerQuest(
            player_quest_id=uuid.uuid4(),
            player_id=test_player.player_id,
            quest_id="quest_new_01",
            status="available",
            objectives_jsonb={},
            rewards_jsonb={},
        )
        session.add(initial_quest)
        await session.commit()

    response = await client.post(
        f"{settings.api_v1_prefix}/player/quests/quest_new_01/accept",
        headers={"Authorization": f"Bearer {player_token}"},
        json={},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["quest_id"] == "quest_new_01"
    assert data["data"]["status"] == "active"


@pytest.mark.asyncio
async def test_accept_quest_already_accepted(client: AsyncClient, player_token: str, test_player, test_player_quest):
    response = await client.post(
        f"{settings.api_v1_prefix}/player/quests/quest_rescue_01/accept",
        headers={"Authorization": f"Bearer {player_token}"},
        json={},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == PlayerErrorCodes.QUEST_ALREADY_ACCEPTED


@pytest.mark.asyncio
async def test_accept_quest_not_found(client: AsyncClient, player_token: str, test_player):
    response = await client.post(
        f"{settings.api_v1_prefix}/player/quests/quest_nonexistent_01/accept",
        headers={"Authorization": f"Bearer {player_token}"},
        json={},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.QUEST_NOT_FOUND


@pytest.mark.asyncio
async def test_update_quest_progress_success(client: AsyncClient, player_token: str, test_player, test_player_quest):
    response = await client.post(
        f"{settings.api_v1_prefix}/player/quests/quest_rescue_01/progress",
        headers={"Authorization": f"Bearer {player_token}"},
        json={"objectives": {"obj1": "已找到村民", "obj2": "护送回村"}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["quest_id"] == "quest_rescue_01"
    assert data["data"]["objectives_jsonb"]["obj1"] == "已找到村民"
    assert data["data"]["objectives_jsonb"]["obj2"] == "护送回村"


@pytest.mark.asyncio
async def test_update_quest_progress_not_active(client: AsyncClient, player_token: str, test_player):
    import uuid
    from app.domain.models import PlayerQuest

    async with TestSessionLocal() as session:
        completed_quest = PlayerQuest(
            player_quest_id=uuid.uuid4(),
            player_id=test_player.player_id,
            quest_id="quest_completed_01",
            status="completed",
            objectives_jsonb={},
            rewards_jsonb={},
        )
        session.add(completed_quest)
        await session.commit()

    response = await client.post(
        f"{settings.api_v1_prefix}/player/quests/quest_completed_01/progress",
        headers={"Authorization": f"Bearer {player_token}"},
        json={"objectives": {"obj1": "test"}},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == PlayerErrorCodes.QUEST_NOT_ACTIVE


@pytest.mark.asyncio
async def test_complete_quest_success(client: AsyncClient, player_token: str, test_player, test_player_quest):
    response = await client.post(
        f"{settings.api_v1_prefix}/player/quests/quest_rescue_01/complete",
        headers={"Authorization": f"Bearer {player_token}"},
        json={},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["quest_id"] == "quest_rescue_01"
    assert data["data"]["status"] == "completed"


@pytest.mark.asyncio
async def test_complete_quest_already_completed(client: AsyncClient, player_token: str, test_player):
    import uuid
    from app.domain.models import PlayerQuest

    async with TestSessionLocal() as session:
        completed_quest = PlayerQuest(
            player_quest_id=uuid.uuid4(),
            player_id=test_player.player_id,
            quest_id="quest_done_01",
            status="completed",
            objectives_jsonb={},
            rewards_jsonb={},
        )
        session.add(completed_quest)
        await session.commit()

    response = await client.post(
        f"{settings.api_v1_prefix}/player/quests/quest_done_01/complete",
        headers={"Authorization": f"Bearer {player_token}"},
        json={},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == PlayerErrorCodes.QUEST_ALREADY_COMPLETED


@pytest.mark.asyncio
async def test_fail_quest_success(client: AsyncClient, player_token: str, test_player, test_player_quest):
    response = await client.post(
        f"{settings.api_v1_prefix}/player/quests/quest_rescue_01/fail",
        headers={"Authorization": f"Bearer {player_token}"},
        json={},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["quest_id"] == "quest_rescue_01"
    assert data["data"]["status"] == "failed"


@pytest.mark.asyncio
async def test_fail_quest_not_active(client: AsyncClient, player_token: str, test_player):
    import uuid
    from app.domain.models import PlayerQuest

    async with TestSessionLocal() as session:
        available_quest = PlayerQuest(
            player_quest_id=uuid.uuid4(),
            player_id=test_player.player_id,
            quest_id="quest_available_01",
            status="available",
            objectives_jsonb={},
            rewards_jsonb={},
        )
        session.add(available_quest)
        await session.commit()

    response = await client.post(
        f"{settings.api_v1_prefix}/player/quests/quest_available_01/fail",
        headers={"Authorization": f"Bearer {player_token}"},
        json={},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == PlayerErrorCodes.QUEST_INVALID_STATE_TRANSITION


@pytest.mark.asyncio
async def test_complete_quest_objectives_incomplete(client: AsyncClient, player_token: str, test_player, test_player_quest_incomplete):
    response = await client.post(
        f"{settings.api_v1_prefix}/player/quests/quest_incomplete_01/complete",
        headers={"Authorization": f"Bearer {player_token}"},
        json={},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == PlayerErrorCodes.QUEST_OBJECTIVES_INCOMPLETE


@pytest.mark.asyncio
async def test_complete_quest_with_rewards(client: AsyncClient, player_token: str, test_player, test_player_quest):
    response = await client.post(
        f"{settings.api_v1_prefix}/player/quests/quest_rescue_01/complete",
        headers={"Authorization": f"Bearer {player_token}"},
        json={},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["quest_id"] == "quest_rescue_01"
    assert data["data"]["status"] == "completed"

    async with TestSessionLocal() as session:
        from app.domain.models import Player
        from sqlalchemy import select
        stmt = select(Player.progress_jsonb, Player.reputation_snapshot).where(
            Player.player_id == test_player.player_id
        )
        result = await session.execute(stmt)
        row = result.first()
        assert row is not None
        progress = row[0]
        reputation = row[1]
        assert progress is not None
        assert progress["resources"]["gold"] == 100
        assert progress["stats"]["experience"] == 50
        assert reputation["iron_guard"] == 10