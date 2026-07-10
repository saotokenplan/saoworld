"""成就系统测试。"""

import pytest
from httpx import AsyncClient

from app.core.errors import PlayerErrorCodes


@pytest.mark.asyncio
async def test_list_achievement_definitions_empty(
    client: AsyncClient, player_token: str
) -> None:
    """测试初始成就列表为空。"""
    response = await client.get(
        "/api/v1/player/achievements",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert "meta" in data
    assert data["data"]["total"] == 0
    assert data["data"]["achievements"] == []


@pytest.mark.asyncio
async def test_get_achievement_not_found(
    client: AsyncClient, player_token: str
) -> None:
    """测试获取不存在的成就返回 404。"""
    response = await client.get(
        "/api/v1/player/achievements/nonexistent_achievement",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.ACHIEVEMENT_NOT_FOUND


@pytest.mark.asyncio
async def test_ops_create_achievement(
    client: AsyncClient, ops_token: str
) -> None:
    """测试运营创建成就定义。"""
    response = await client.post(
        "/api/v1/ops/achievements",
        json={
            "achievement_key": "test_achievement_001",
            "name": "测试成就",
            "description": "这是一个测试成就",
            "rarity": "common",
            "category": "quest",
            "points": 10,
            "reward_jsonb": {"coins": 100},
        },
        headers={
            "Authorization": f"Bearer {ops_token}",
            "X-Trace-Id": "trace_test_achievement_create",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["achievement_key"] == "test_achievement_001"
    assert data["data"]["name"] == "测试成就"
    assert data["data"]["rarity"] == "common"
    assert data["data"]["category"] == "quest"
    assert data["data"]["points"] == 10
    assert data["data"]["is_active"] is True


@pytest.mark.asyncio
async def test_ops_create_achievement_duplicate_key(
    client: AsyncClient, ops_token: str
) -> None:
    """测试创建重复 key 的成就返回 409。"""
    await client.post(
        "/api/v1/ops/achievements",
        json={
            "achievement_key": "test_dup_achievement",
            "name": "测试重复成就",
            "description": "测试",
            "rarity": "rare",
            "category": "exploration",
            "points": 50,
        },
        headers={"Authorization": f"Bearer {ops_token}"},
    )

    response = await client.post(
        "/api/v1/ops/achievements",
        json={
            "achievement_key": "test_dup_achievement",
            "name": "另一个同名成就",
            "description": "测试重复",
            "rarity": "epic",
            "category": "combat",
            "points": 100,
        },
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == PlayerErrorCodes.ACHIEVEMENT_KEY_EXISTS


@pytest.mark.asyncio
async def test_list_achievements_with_filter(
    client: AsyncClient, ops_token: str, player_token: str
) -> None:
    """测试按分类和稀有度筛选成就列表。"""
    for i in range(3):
        await client.post(
            "/api/v1/ops/achievements",
            json={
                "achievement_key": f"filter_test_{i}",
                "name": f"筛选测试成就{i}",
                "description": f"测试筛选{i}",
                "rarity": "rare" if i % 2 == 0 else "common",
                "category": "quest" if i < 2 else "exploration",
                "points": 10 * (i + 1),
            },
            headers={"Authorization": f"Bearer {ops_token}"},
        )

    response = await client.get(
        "/api/v1/player/achievements?category=quest",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] >= 2


@pytest.mark.asyncio
async def test_get_player_achievements_empty(
    client: AsyncClient, test_player, player_token: str
) -> None:
    """测试初始玩家成就列表为空。"""
    response = await client.get(
        "/api/v1/player/me/achievements",
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Player-Id": "00000000-0000-0000-0000-000000000001",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 0
    assert data["data"]["achievements"] == []


@pytest.mark.asyncio
async def test_ops_unlock_achievement(
    client: AsyncClient, test_player, ops_token: str, player_token: str
) -> None:
    """测试运营解锁玩家成就。"""
    player_id = "00000000-0000-0000-0000-000000000001"

    await client.post(
        "/api/v1/ops/achievements",
        json={
            "achievement_key": "unlock_test_001",
            "name": "解锁测试成就",
            "description": "测试解锁",
            "rarity": "common",
            "category": "quest",
            "points": 10,
        },
        headers={"Authorization": f"Bearer {ops_token}"},
    )

    response = await client.post(
        f"/api/v1/ops/players/{player_id}/achievements/unlock_test_001/unlock",
        json={"source": "ops", "source_id": "test_unlock_001"},
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "unlock-achievement-001",
            "X-Trace-Id": "trace_test_unlock",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["achievement_key"] == "unlock_test_001"
    assert data["data"]["reward_claimed"] is False

    query_response = await client.get(
        "/api/v1/player/me/achievements",
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Player-Id": player_id,
        },
    )
    assert query_response.status_code == 200
    query_data = query_response.json()
    assert query_data["data"]["total"] == 1
    assert query_data["data"]["achievements"][0]["achievement_key"] == "unlock_test_001"


@pytest.mark.asyncio
async def test_claim_achievement_reward(
    client: AsyncClient, test_player, ops_token: str, player_token: str
) -> None:
    """测试领取成就奖励。"""
    player_id = "00000000-0000-0000-0000-000000000001"

    await client.post(
        "/api/v1/ops/achievements",
        json={
            "achievement_key": "reward_test_001",
            "name": "奖励测试成就",
            "description": "测试奖励领取",
            "rarity": "rare",
            "category": "quest",
            "points": 50,
            "reward_jsonb": {"coins": 500, "exp": 100},
        },
        headers={"Authorization": f"Bearer {ops_token}"},
    )

    await client.post(
        f"/api/v1/ops/players/{player_id}/achievements/reward_test_001/unlock",
        json={"source": "system"},
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "unlock-reward-test-001",
        },
    )

    claim_response = await client.post(
        "/api/v1/player/me/achievements/reward_test_001/claim",
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Player-Id": player_id,
            "X-Trace-Id": "trace_test_claim_reward",
        },
    )
    assert claim_response.status_code == 200
    claim_data = claim_response.json()
    assert claim_data["data"]["reward_claimed"] is True
    assert claim_data["data"]["claimed_at"] is not None

    second_claim_response = await client.post(
        "/api/v1/player/me/achievements/reward_test_001/claim",
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Player-Id": player_id,
        },
    )
    assert second_claim_response.status_code == 409
    second_claim_data = second_claim_response.json()
    assert second_claim_data["code"] == PlayerErrorCodes.ACHIEVEMENT_REWARD_ALREADY_CLAIMED


@pytest.mark.asyncio
async def test_unlock_achievement_player_not_found(
    client: AsyncClient, ops_token: str
) -> None:
    """测试为不存在的玩家解锁成就返回 404。"""
    fake_player_id = "00000000-0000-0000-0000-999999999999"

    await client.post(
        "/api/v1/ops/achievements",
        json={
            "achievement_key": "notfound_test",
            "name": "不存在测试",
            "description": "测试",
            "rarity": "common",
            "category": "quest",
            "points": 10,
        },
        headers={"Authorization": f"Bearer {ops_token}"},
    )

    response = await client.post(
        f"/api/v1/ops/players/{fake_player_id}/achievements/notfound_test/unlock",
        json={"source": "system"},
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "unlock-notfound-001",
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.PLAYER_NOT_FOUND


@pytest.mark.asyncio
async def test_unlock_nonexistent_achievement(
    client: AsyncClient, test_player, ops_token: str
) -> None:
    """测试解锁不存在的成就返回 404。"""
    player_id = "00000000-0000-0000-0000-000000000001"
    response = await client.post(
        f"/api/v1/ops/players/{player_id}/achievements/nonexistent_ach/unlock",
        json={"source": "system"},
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "unlock-nonexistent-001",
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.ACHIEVEMENT_NOT_FOUND
