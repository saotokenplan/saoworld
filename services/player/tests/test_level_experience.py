import pytest
from httpx import AsyncClient

from app.schemas.player import (
    get_experience_for_level,
    get_level_from_experience,
    get_level_progress,
    MAX_PLAYER_LEVEL,
    BASE_EXPERIENCE,
    EXPERIENCE_GROWTH_RATE,
)

TEST_PLAYER_ID = "00000000-0000-0000-0000-000000000001"


@pytest.mark.asyncio
async def test_get_level_initial_state(
    client: AsyncClient, test_player, player_token: str
):
    response = await client.get(
        "/api/v1/player/level",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["level"] == 1
    assert data["experience_points"] == 0
    assert data["next_level_experience"] > 0
    assert data["level_progress"] == 0.0


@pytest.mark.asyncio
async def test_get_level_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/player/level")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ops_add_experience_success(
    client: AsyncClient, test_player, ops_token: str
):
    response = await client.post(
        f"/api/v1/ops/players/{TEST_PLAYER_ID}/experience",
        json={
            "amount": 150,
            "source": "ops",
            "reason": "运营调整测试",
        },
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-exp-001",
            "X-Trace-Id": "trace_test_exp",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["experience_points"] == 150
    assert data["level"] >= 1
    assert data["level_progress"] > 0


@pytest.mark.asyncio
async def test_ops_add_experience_player_not_found(
    client: AsyncClient, ops_token: str
):
    import uuid
    fake_id = str(uuid.uuid4())
    response = await client.post(
        f"/api/v1/ops/players/{fake_id}/experience",
        json={"amount": 100, "source": "ops"},
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-exp-002",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ops_add_experience_unauthorized(client: AsyncClient):
    response = await client.post(
        f"/api/v1/ops/players/{TEST_PLAYER_ID}/experience",
        json={"amount": 100},
        headers={"Idempotency-Key": "test-exp-003"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ops_add_experience_player_forbidden(
    client: AsyncClient, test_player, player_token: str
):
    response = await client.post(
        f"/api/v1/ops/players/{TEST_PLAYER_ID}/experience",
        json={"amount": 100},
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "test-exp-004",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_complete_quest_grants_experience(
    client: AsyncClient, test_player, player_token: str, ops_token: str
):
    quest_id = "quest_exp_test_01"
    create_response = await client.post(
        f"/api/v1/ops/players/{TEST_PLAYER_ID}/quests",
        json={
            "quest_id": quest_id,
            "status": "active",
            "objectives_jsonb": {
                "objectives": [
                    {"id": "obj1", "text": "测试目标", "completed": True}
                ]
            },
            "rewards_jsonb": {
                "experience_points": 200,
                "gold": 50,
                "contribution_points": 10,
            },
        },
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "create-exp-quest-001",
        },
    )
    assert create_response.status_code == 201

    level_before_response = await client.get(
        "/api/v1/player/level",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    level_before = level_before_response.json()["data"]

    complete_response = await client.post(
        f"/api/v1/player/quests/{quest_id}/complete",
        json={"completion_note": "test"},
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "complete-exp-001",
        },
    )
    assert complete_response.status_code == 200

    level_after_response = await client.get(
        "/api/v1/player/level",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    level_after = level_after_response.json()["data"]

    assert level_after["experience_points"] > level_before["experience_points"]
    assert level_after["experience_points"] - level_before["experience_points"] == 200


def test_get_experience_for_level_one():
    assert get_experience_for_level(1) == 0


def test_get_experience_for_level_two():
    assert get_experience_for_level(2) == BASE_EXPERIENCE


def test_get_level_from_experience_zero():
    assert get_level_from_experience(0) == 1


def test_get_level_from_experience_negative():
    assert get_level_from_experience(-100) == 1


def test_get_level_from_experience_at_threshold():
    exp_for_2 = get_experience_for_level(2)
    assert get_level_from_experience(exp_for_2 - 1) == 1
    assert get_level_from_experience(exp_for_2) == 2


def test_get_level_progress_level_one():
    level, next_exp, progress = get_level_progress(0)
    assert level == 1
    assert progress == 0.0
    assert next_exp == get_experience_for_level(2)


def test_get_level_progress_halfway():
    exp_for_2 = get_experience_for_level(2)
    exp_for_3 = get_experience_for_level(3)
    mid_exp = (exp_for_2 + exp_for_3) // 2
    level, next_exp, progress = get_level_progress(mid_exp)
    assert level == 2
    assert next_exp == exp_for_3
    assert 0.0 < progress < 1.0


def test_get_level_progress_max_level():
    total_exp = 0
    for i in range(1, MAX_PLAYER_LEVEL + 1):
        total_exp += int(BASE_EXPERIENCE * (EXPERIENCE_GROWTH_RATE ** (i - 1)))
    level, next_exp, progress = get_level_progress(total_exp * 2)
    assert level == MAX_PLAYER_LEVEL
    assert progress == 1.0


@pytest.mark.asyncio
async def test_profile_includes_level_info(
    client: AsyncClient, test_player, player_token: str
):
    response = await client.get(
        "/api/v1/player/profile",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "level" in data
    assert "experience_points" in data
    assert "next_level_experience" in data
    assert "level_progress" in data
    assert data["level"] >= 1
    assert data["experience_points"] >= 0


@pytest.mark.asyncio
async def test_level_up_grants_contribution(
    client: AsyncClient, test_player, ops_token: str
):
    exp_for_3 = get_experience_for_level(3)

    player_before_response = await client.get(
        f"/api/v1/ops/players/{TEST_PLAYER_ID}",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    contrib_before = player_before_response.json()["data"]["contribution_points"]

    response = await client.post(
        f"/api/v1/ops/players/{TEST_PLAYER_ID}/experience",
        json={
            "amount": exp_for_3 + 50,
            "source": "ops",
        },
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-levelup-001",
            "X-Trace-Id": "trace_test_levelup",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["level"] >= 3

    player_after_response = await client.get(
        f"/api/v1/ops/players/{TEST_PLAYER_ID}",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    contrib_after = player_after_response.json()["data"]["contribution_points"]

    expected_rewards = sum(level * 10 for level in range(2, data["level"] + 1))
    assert contrib_after - contrib_before >= expected_rewards
