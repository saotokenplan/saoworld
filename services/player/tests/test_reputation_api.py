import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.core.errors import PlayerErrorCodes
from tests.conftest import TestSessionLocal


@pytest.mark.asyncio
async def test_get_region_reputation_success(client: AsyncClient, player_token: str, test_player, test_player_region):
    response = await client.get(
        f"{settings.api_v1_prefix}/player/reputation/region_wasteland_01",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert data["data"]["region_id"] == "region_wasteland_01"
    assert data["data"]["reputation"] == 50
    assert data["data"]["reputation_level"] == "neutral"
    assert "next_level_threshold" in data["data"]
    assert "current_level_progress" in data["data"]


@pytest.mark.asyncio
async def test_get_region_reputation_no_record(client: AsyncClient, player_token: str, test_player):
    response = await client.get(
        f"{settings.api_v1_prefix}/player/reputation/region_unknown_01",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["reputation"] == 0
    assert data["data"]["reputation_level"] == "neutral"


@pytest.mark.asyncio
async def test_get_region_reputation_unauthorized(client: AsyncClient):
    response = await client.get(
        f"{settings.api_v1_prefix}/player/reputation/region_wasteland_01",
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_all_reputation_success(client: AsyncClient, player_token: str, test_player, test_player_region):
    response = await client.get(
        f"{settings.api_v1_prefix}/player/reputation",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1
    assert "meta" in data
    assert data["meta"]["total"] >= 1


@pytest.mark.asyncio
async def test_get_all_reputation_empty(client: AsyncClient, player_token: str, test_player):
    response = await client.get(
        f"{settings.api_v1_prefix}/player/reputation",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["data"], list)
    assert data["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_get_all_reputation_pagination(client: AsyncClient, player_token: str, test_player, test_player_region):
    response = await client.get(
        f"{settings.api_v1_prefix}/player/reputation?limit=1&offset=0",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["limit"] == 1
    assert data["meta"]["offset"] == 0


@pytest.mark.asyncio
async def test_ops_adjust_reputation_add(client: AsyncClient, ops_token: str, test_player):
    response = await client.post(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}/reputation/region_wasteland_01/adjust",
        json={"amount": 100, "reason": "任务奖励"},
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-adjust-rep-001",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["region_id"] == "region_wasteland_01"
    assert data["data"]["reputation"] == 100
    assert data["data"]["reputation_level"] == "neutral"


@pytest.mark.asyncio
async def test_ops_adjust_reputation_remove(client: AsyncClient, ops_token: str, test_player, test_player_region):
    response = await client.post(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}/reputation/region_wasteland_01/adjust",
        json={"amount": -20, "reason": "违规行为"},
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-adjust-rep-002",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["reputation"] == 30


@pytest.mark.asyncio
async def test_ops_adjust_reputation_player_not_found(client: AsyncClient, ops_token: str):
    import uuid
    fake_id = uuid.uuid4()
    response = await client.post(
        f"{settings.api_v1_prefix}/ops/players/{fake_id}/reputation/region_wasteland_01/adjust",
        json={"amount": 100, "reason": "测试"},
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-adjust-rep-003",
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.PLAYER_NOT_FOUND


@pytest.mark.asyncio
async def test_ops_adjust_reputation_unauthorized(client: AsyncClient, test_player):
    response = await client.post(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}/reputation/region_wasteland_01/adjust",
        json={"amount": 100},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ops_adjust_reputation_player_forbidden(client: AsyncClient, player_token: str, test_player):
    response = await client.post(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}/reputation/region_wasteland_01/adjust",
        json={"amount": 100},
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "test-adjust-rep-004",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_reputation_level_calculation_hostile(client: AsyncClient, ops_token: str, test_player):
    response = await client.post(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}/reputation/region_test_01/adjust",
        json={"amount": -5000, "reason": "测试"},
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-adjust-rep-005",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["reputation_level"] == "hostile"


@pytest.mark.asyncio
async def test_reputation_level_calculation_friendly(client: AsyncClient, ops_token: str, test_player):
    response = await client.post(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}/reputation/region_test_02/adjust",
        json={"amount": 5000, "reason": "测试"},
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-adjust-rep-006",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["reputation_level"] == "friendly"


@pytest.mark.asyncio
async def test_reputation_level_calculation_exalted(client: AsyncClient, ops_token: str, test_player):
    response = await client.post(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}/reputation/region_test_03/adjust",
        json={"amount": 42000, "reason": "测试"},
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-adjust-rep-007",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["reputation_level"] == "exalted"


@pytest.mark.asyncio
async def test_complete_quest_grants_reputation(client: AsyncClient, player_token: str, test_player, test_player_quest):
    response = await client.post(
        f"{settings.api_v1_prefix}/player/quests/quest_rescue_01/complete",
        json={},
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "test-complete-quest-rep-001",
        },
    )
    assert response.status_code == 200

    rep_response = await client.get(
        f"{settings.api_v1_prefix}/player/reputation/iron_guard",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert rep_response.status_code == 200
    rep_data = rep_response.json()
    assert rep_data["data"]["reputation"] == 10


@pytest.mark.asyncio
async def test_check_reputation_unlock_various_levels():
    from app.schemas.player import (
        ReputationUnlockCondition,
        UnlockType,
        ReputationLevel,
        check_reputation_unlock,
        get_next_unlock_threshold,
    )

    condition_min_rep = ReputationUnlockCondition(
        unlock_type=UnlockType.REGION_UNLOCK,
        min_reputation=3000,
    )
    assert check_reputation_unlock(2000, condition_min_rep) is False
    assert check_reputation_unlock(3000, condition_min_rep) is True
    assert check_reputation_unlock(5000, condition_min_rep) is True

    condition_level = ReputationUnlockCondition(
        unlock_type=UnlockType.REGION_UNLOCK,
        required_level=ReputationLevel.FRIENDLY,
    )
    assert check_reputation_unlock(2999, condition_level) is False
    assert check_reputation_unlock(3000, condition_level) is True
    assert check_reputation_unlock(9000, condition_level) is True

    condition_npc = ReputationUnlockCondition(
        unlock_type=UnlockType.NPC_INTERACTION,
        min_reputation=1000,
    )
    assert check_reputation_unlock(500, condition_npc) is False
    assert check_reputation_unlock(1500, condition_npc) is True

    next_thresh, progress = get_next_unlock_threshold(0)
    assert next_thresh >= 0
    assert 0.0 <= progress <= 1.0

    next_thresh, progress = get_next_unlock_threshold(3000)
    assert next_thresh > 3000
    assert progress == 0.0 or progress > 0.0


@pytest.mark.asyncio
async def test_reputation_unlocks_region(client: AsyncClient, player_token: str, test_player):
    from app.domain.models import PlayerRegion
    import uuid

    async with TestSessionLocal() as session:
        player_region = PlayerRegion(
            player_region_id=uuid.uuid4(),
            player_id=test_player.player_id,
            region_id="region_test_unlock_01",
            unlocked_at=None,
            reputation=2990,
        )
        session.add(player_region)
        await session.commit()

    from app.domain.models import PlayerQuest
    quest = PlayerQuest(
        player_quest_id=uuid.uuid4(),
        player_id=test_player.player_id,
        quest_id="quest_unlock_test_01",
        status="active",
        objectives_jsonb={"objectives": [{"id": "obj1", "completed": True}]},
        rewards_jsonb={"reputation": {"region_test_unlock_01": 20}},
    )
    async with TestSessionLocal() as session:
        session.add(quest)
        await session.commit()

    response = await client.post(
        f"{settings.api_v1_prefix}/player/quests/quest_unlock_test_01/complete",
        json={},
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "test-unlock-region-001",
        },
    )
    assert response.status_code == 200

    regions_response = await client.get(
        f"{settings.api_v1_prefix}/player/regions",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert regions_response.status_code == 200
    regions_data = regions_response.json()
    unlocked_regions = [
        r for r in regions_data["data"]
        if r["region_id"] == "region_test_unlock_01"
    ]
    assert len(unlocked_regions) == 1
    assert unlocked_regions[0]["unlocked_at"] is not None


@pytest.mark.asyncio
async def test_reputation_locked_error():
    from app.core.errors import PlayerErrorCodes
    from app.schemas.player import (
        ReputationUnlockCondition,
        UnlockType,
        check_reputation_unlock,
    )

    assert PlayerErrorCodes.REPUTATION_LOCKED == "REPUTATION_LOCKED"

    condition = ReputationUnlockCondition(
        unlock_type=UnlockType.REGION_UNLOCK,
        min_reputation=3000,
    )
    assert check_reputation_unlock(1000, condition) is False
    assert check_reputation_unlock(5000, condition) is True
