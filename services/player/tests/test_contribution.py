"""贡献度系统测试。"""

import pytest
from httpx import AsyncClient

from app.core.contribution import calculate_vote_weight_multiplier
from app.core.errors import PlayerErrorCodes


@pytest.mark.asyncio
async def test_get_player_contribution_initial_empty(
    client: AsyncClient, test_player, player_token: str
) -> None:
    """测试初始贡献度查询返回 envelope 且总分为 0。"""
    response = await client.get(
        "/api/v1/player/contribution",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert "meta" in data
    assert data["data"]["contribution_points"] == 0
    assert data["data"]["contributions"] == []
    assert data["data"]["total"] == 0


@pytest.mark.asyncio
async def test_ops_add_contribution_and_query(
    client: AsyncClient, test_player, ops_token: str, player_token: str
) -> None:
    """测试运营增加贡献度后玩家查询返回正确总分与流水。"""
    player_id = "00000000-0000-0000-0000-000000000001"
    response = await client.post(
        f"/api/v1/ops/players/{player_id}/contribution",
        json={
            "amount": 150,
            "source": "ops",
            "source_id": "ops_event_001",
            "description": "运营补偿",
        },
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "add-contribution-001",
            "X-Trace-Id": "trace_test_contribution",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["amount"] == 150
    assert data["data"]["source"] == "ops"
    assert data["data"]["source_id"] == "ops_event_001"

    query_response = await client.get(
        "/api/v1/player/contribution",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert query_response.status_code == 200
    query_data = query_response.json()
    assert query_data["data"]["contribution_points"] == 150
    assert len(query_data["data"]["contributions"]) == 1
    assert query_data["data"]["contributions"][0]["amount"] == 150
    assert query_data["data"]["total"] == 1


@pytest.mark.asyncio
async def test_ops_add_contribution_player_not_found(
    client: AsyncClient, ops_token: str
) -> None:
    """测试为不存在的玩家增加贡献度返回 404。"""
    fake_player_id = "00000000-0000-0000-0000-999999999999"
    response = await client.post(
        f"/api/v1/ops/players/{fake_player_id}/contribution",
        json={"amount": 100, "source": "ops"},
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "add-contribution-notfound-001",
            "X-Trace-Id": "trace_test_contribution_notfound",
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.CONTRIBUTION_PLAYER_NOT_FOUND


@pytest.mark.asyncio
async def test_ops_add_contribution_invalid_amount(
    client: AsyncClient, test_player, ops_token: str
) -> None:
    """测试无效贡献度数值返回 422。"""
    player_id = "00000000-0000-0000-0000-000000000001"
    response = await client.post(
        f"/api/v1/ops/players/{player_id}/contribution",
        json={"amount": 0, "source": "ops"},
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "add-contribution-invalid-001",
            "X-Trace-Id": "trace_test_contribution_invalid",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_complete_quest_grants_contribution_points(
    client: AsyncClient, test_player, player_token: str
) -> None:
    """测试任务完成时自动发放 rewards_jsonb 中配置的贡献度。"""
    player_id = "00000000-0000-0000-0000-000000000001"

    # 创建一个带有 contribution_points 奖励的任务
    create_response = await client.post(
        f"/api/v1/ops/players/{player_id}/quests",
        json={
            "quest_id": "quest_contribution_01",
            "status": "active",
            "objectives_jsonb": {
                "objectives": [{"id": "obj1", "text": "测试目标", "completed": True}]
            },
            "rewards_jsonb": {
                "gold": 50,
                "contribution_points": 200,
            },
        },
        headers={
            "Authorization": f"Bearer {create_test_token_for_ops()}",
            "Idempotency-Key": "create-quest-contribution-001",
            "X-Trace-Id": "trace_test_quest_contribution",
        },
    )
    assert create_response.status_code == 201

    complete_response = await client.post(
        "/api/v1/player/quests/quest_contribution_01/complete",
        json={},
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "complete-quest-contribution-001",
        },
    )
    assert complete_response.status_code == 200

    query_response = await client.get(
        "/api/v1/player/contribution",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert query_response.status_code == 200
    query_data = query_response.json()
    assert query_data["data"]["contribution_points"] == 200
    assert len(query_data["data"]["contributions"]) == 1
    contribution = query_data["data"]["contributions"][0]
    assert contribution["amount"] == 200
    assert contribution["source"] == "quest"
    assert contribution["source_id"] == "quest_contribution_01"


def create_test_token_for_ops() -> str:
    """Helper to create ops token for nested async tests."""
    from app.core.auth import create_test_token
    from app.schemas.auth import Role

    return create_test_token(user_id="test_ops_user", role=Role.OPS)


@pytest.mark.asyncio
async def test_contribution_list_pagination(
    client: AsyncClient, test_player, ops_token: str, player_token: str
) -> None:
    """测试贡献度流水支持 limit/offset 分页。"""
    player_id = "00000000-0000-0000-0000-000000000001"
    for i in range(3):
        response = await client.post(
            f"/api/v1/ops/players/{player_id}/contribution",
            json={"amount": 10, "source": "ops"},
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": f"add-contribution-paging-{i:03d}",
                "X-Trace-Id": f"trace_test_paging_{i}",
            },
        )
        assert response.status_code == 201

    response = await client.get(
        "/api/v1/player/contribution?limit=2&offset=0",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 3
    assert len(data["data"]["contributions"]) == 2
    assert data["meta"]["limit"] == 2
    assert data["meta"]["offset"] == 0

    response = await client.get(
        "/api/v1/player/contribution?limit=2&offset=2",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["contributions"]) == 1


@pytest.mark.parametrize(
    "points,expected",
    [
        (0, 1.0),
        (500, 1.05),
        (1000, 1.1),
        (2000, 1.2),
        (10000, 1.2),
    ],
)
def test_calculate_vote_weight_multiplier(points: int, expected: float) -> None:
    """测试贡献度到投票权重倍率的边界值。"""
    assert calculate_vote_weight_multiplier(points) == expected
