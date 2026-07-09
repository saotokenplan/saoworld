import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_npcs_no_token_returns_401(client: AsyncClient):
    response = await client.get("/api/v1/world/npcs")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_npcs_invalid_token_returns_401(client: AsyncClient):
    response = await client.get(
        "/api/v1/world/npcs",
        headers={"Authorization": "Bearer invalid.token.value"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_npcs_success_envelope(
    client: AsyncClient, player_token: str
):
    response = await client.get(
        "/api/v1/world/npcs",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "request_id" in body
    assert "data" in body
    assert "npcs" in body["data"]
    assert "total" in body["data"]
    assert "meta" in body
    assert body["meta"]["total"] == body["data"]["total"]


@pytest.mark.asyncio
async def test_list_npcs_pagination(
    client: AsyncClient, player_token: str
):
    response = await client.get(
        "/api/v1/world/npcs",
        params={"limit": 5, "offset": 0},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["limit"] == 5
    assert body["meta"]["offset"] == 0
    assert len(body["data"]["npcs"]) <= 5


@pytest.mark.asyncio
async def test_list_npcs_chapter_filter(
    client: AsyncClient, player_token: str
):
    response = await client.get(
        "/api/v1/world/npcs",
        params={"chapter_id": "ch_99_nonexistent"},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["total"] == 0
    assert body["data"]["npcs"] == []


@pytest.mark.asyncio
async def test_get_npc_by_id_not_found(
    client: AsyncClient, player_token: str
):
    response = await client.get(
        f"/api/v1/world/npcs/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "NPC_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_npc_by_key_not_found(
    client: AsyncClient, player_token: str
):
    response = await client.get(
        "/api/v1/world/npcs/by-key/npc_nonexistent_xxx",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "NPC_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_npc_success(client: AsyncClient, ops_token: str):
    response = await client.post(
        "/api/v1/ops/world/npcs",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-npc-create-001",
            "X-Trace-Id": "trace_npc_001",
        },
        json={
            "npc_key": "npc_test_ironward_leader",
            "chapter_id": "ch_01",
            "name": "钢铁守望队长",
            "title": "守望队长",
            "faction_key": "faction_ironward",
            "role": "leader",
            "location_key": "region_ironward_01",
            "description": "一个测试 NPC",
            "personality": ["正直", "严肃"],
            "dialogues": [
                {"trigger": "greeting", "text": "你好，旅人。"}
            ],
            "related_quests": ["quest_test_01"],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert "npc_id" in body["data"]
    assert body["data"]["npc_key"] == "npc_test_ironward_leader"
    assert body["data"]["chapter_id"] == "ch_01"
    assert body["data"]["name"] == "钢铁守望队长"
    assert body["trace_id"] == "trace_npc_001"


@pytest.mark.asyncio
async def test_create_npc_player_role_forbidden(
    client: AsyncClient, player_token: str
):
    response = await client.post(
        "/api/v1/ops/world/npcs",
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "test-npc-create-002",
        },
        json={
            "npc_key": "npc_test_should_fail",
            "chapter_id": "ch_01",
            "name": "Should Fail",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_npc_missing_title_returns_400(
    client: AsyncClient, ops_token: str
):
    response = await client.post(
        "/api/v1/ops/world/npcs",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-npc-create-003",
        },
        json={
            "npc_key": "npc_test_no_name",
            "chapter_id": "ch_01",
        },
    )
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_create_npc_duplicate_key_returns_409(
    client: AsyncClient, ops_token: str
):
    payload = {
        "npc_key": "npc_test_duplicate_key",
        "chapter_id": "ch_01",
        "name": "重复测试 NPC",
    }
    headers = {
        "Authorization": f"Bearer {ops_token}",
        "Idempotency-Key": "test-npc-create-004",
    }
    first = await client.post("/api/v1/ops/world/npcs", json=payload, headers=headers)
    assert first.status_code == 201

    second = await client.post(
        "/api/v1/ops/world/npcs",
        json=payload,
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-npc-create-005",
        },
    )
    assert second.status_code == 409
    body = second.json()
    assert body["code"] == "NPC_KEY_EXISTS"


@pytest.mark.asyncio
async def test_npc_create_then_get_by_key(
    client: AsyncClient, ops_token: str, player_token: str
):
    create_resp = await client.post(
        "/api/v1/ops/world/npcs",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-npc-create-006",
        },
        json={
            "npc_key": "npc_test_get_by_key",
            "chapter_id": "ch_01",
            "name": "按 key 查询的 NPC",
        },
    )
    assert create_resp.status_code == 201

    get_resp = await client.get(
        "/api/v1/world/npcs/by-key/npc_test_get_by_key",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["data"]["npc_key"] == "npc_test_get_by_key"
    assert body["data"]["name"] == "按 key 查询的 NPC"
