import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_quests_no_token_returns_401(client: AsyncClient):
    response = await client.get("/api/v1/world/quests")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_quests_invalid_token_returns_401(client: AsyncClient):
    response = await client.get(
        "/api/v1/world/quests",
        headers={"Authorization": "Bearer invalid.token.value"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_quests_success_envelope(
    client: AsyncClient, player_token: str
):
    response = await client.get(
        "/api/v1/world/quests",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "request_id" in body
    assert "data" in body
    assert "quests" in body["data"]
    assert "total" in body["data"]
    assert "meta" in body
    assert body["meta"]["total"] == body["data"]["total"]


@pytest.mark.asyncio
async def test_list_quests_pagination(
    client: AsyncClient, player_token: str
):
    response = await client.get(
        "/api/v1/world/quests",
        params={"limit": 5, "offset": 0},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["limit"] == 5
    assert body["meta"]["offset"] == 0
    assert len(body["data"]["quests"]) <= 5


@pytest.mark.asyncio
async def test_list_quests_chapter_filter(
    client: AsyncClient, player_token: str
):
    response = await client.get(
        "/api/v1/world/quests",
        params={"chapter_id": "ch_99_nonexistent"},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["total"] == 0


@pytest.mark.asyncio
async def test_list_quests_type_filter(
    client: AsyncClient, player_token: str
):
    response = await client.get(
        "/api/v1/world/quests",
        params={"quest_type": "daily"},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["total"] == 0


@pytest.mark.asyncio
async def test_list_quests_invalid_type_returns_422(
    client: AsyncClient, player_token: str
):
    response = await client.get(
        "/api/v1/world/quests",
        params={"quest_type": "invalid_type"},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_quest_by_id_not_found(
    client: AsyncClient, player_token: str
):
    response = await client.get(
        f"/api/v1/world/quests/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "QUEST_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_quest_by_key_not_found(
    client: AsyncClient, player_token: str
):
    response = await client.get(
        "/api/v1/world/quests/by-key/quest_nonexistent_xxx",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "QUEST_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_quest_success(client: AsyncClient, ops_token: str):
    response = await client.post(
        "/api/v1/ops/world/quests",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-quest-create-001",
            "X-Trace-Id": "trace_quest_001",
        },
        json={
            "quest_key": "quest_test_main_ch01_start",
            "chapter_id": "ch_01",
            "title": "启程：裂隙边境",
            "description": "玩家从守望队接到的第一个任务",
            "quest_type": "main",
            "region_key": "region_ironward_01",
            "start_npc_key": "npc_test_ironward_leader",
            "end_npc_key": "npc_test_ironward_leader",
            "objectives": [
                {"type": "kill", "target": "monster_test_01", "count": 3}
            ],
            "rewards": {"exp": 100, "gold": 50},
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert "quest_id" in body["data"]
    assert body["data"]["quest_key"] == "quest_test_main_ch01_start"
    assert body["data"]["quest_type"] == "main"
    assert body["trace_id"] == "trace_quest_001"


@pytest.mark.asyncio
async def test_create_quest_player_role_forbidden(
    client: AsyncClient, player_token: str
):
    response = await client.post(
        "/api/v1/ops/world/quests",
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "test-quest-create-002",
        },
        json={
            "quest_key": "quest_test_should_fail",
            "chapter_id": "ch_01",
            "title": "Should Fail",
            "quest_type": "side",
            "objectives": [{"type": "collect", "item": "stone", "count": 1}],
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_quest_missing_title_returns_400_or_422(
    client: AsyncClient, ops_token: str
):
    response = await client.post(
        "/api/v1/ops/world/quests",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-quest-create-003",
        },
        json={
            "quest_key": "quest_test_no_title",
            "chapter_id": "ch_01",
            "quest_type": "side",
            "objectives": [{"type": "collect"}],
        },
    )
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_create_quest_empty_objectives_returns_422(
    client: AsyncClient, ops_token: str
):
    response = await client.post(
        "/api/v1/ops/world/quests",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-quest-create-004",
        },
        json={
            "quest_key": "quest_test_no_objectives",
            "chapter_id": "ch_01",
            "title": "无目标",
            "quest_type": "side",
            "objectives": [],
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_quest_duplicate_key_returns_409(
    client: AsyncClient, ops_token: str
):
    payload = {
        "quest_key": "quest_test_duplicate_key",
        "chapter_id": "ch_01",
        "title": "重复测试",
        "quest_type": "side",
        "objectives": [{"type": "collect", "item": "stone", "count": 1}],
    }
    headers = {
        "Authorization": f"Bearer {ops_token}",
        "Idempotency-Key": "test-quest-create-005",
    }
    first = await client.post(
        "/api/v1/ops/world/quests", json=payload, headers=headers
    )
    assert first.status_code == 201

    second = await client.post(
        "/api/v1/ops/world/quests",
        json=payload,
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-quest-create-006",
        },
    )
    assert second.status_code == 409
    body = second.json()
    assert body["code"] == "QUEST_KEY_EXISTS"


@pytest.mark.asyncio
async def test_quest_create_then_get_by_key(
    client: AsyncClient, ops_token: str, player_token: str
):
    create_resp = await client.post(
        "/api/v1/ops/world/quests",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-quest-create-007",
        },
        json={
            "quest_key": "quest_test_get_by_key",
            "chapter_id": "ch_01",
            "title": "按 key 查询的 Quest",
            "quest_type": "event",
            "objectives": [{"type": "explore", "region": "region_01"}],
        },
    )
    assert create_resp.status_code == 201

    get_resp = await client.get(
        "/api/v1/world/quests/by-key/quest_test_get_by_key",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["data"]["quest_key"] == "quest_test_get_by_key"
    assert body["data"]["title"] == "按 key 查询的 Quest"
    assert body["data"]["quest_type"] == "event"


@pytest.mark.asyncio
async def test_get_quest_by_key_chapter_filter(
    client: AsyncClient, ops_token: str, player_token: str
):
    await client.post(
        "/api/v1/ops/world/quests",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-quest-create-008",
        },
        json={
            "quest_key": "quest_test_chapter_filter",
            "chapter_id": "ch_filter",
            "title": "章节过滤",
            "quest_type": "side",
            "objectives": [{"type": "collect"}],
        },
    )

    wrong = await client.get(
        "/api/v1/world/quests/by-key/quest_test_chapter_filter",
        params={"chapter_id": "ch_other"},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert wrong.status_code == 404

    correct = await client.get(
        "/api/v1/world/quests/by-key/quest_test_chapter_filter",
        params={"chapter_id": "ch_filter"},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert correct.status_code == 200
