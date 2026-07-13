"""装备系统 API 测试。"""

import pytest
from httpx import AsyncClient

from app.core.errors import PlayerErrorCodes


@pytest.mark.asyncio
async def test_get_player_equipment_empty(
    client: AsyncClient, test_player, player_token: str
) -> None:
    """测试查询空装备栏。"""
    response = await client.get(
        "/api/v1/player/equipment",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert data["data"] == []


@pytest.mark.asyncio
async def test_get_equipment_unauthorized(client: AsyncClient) -> None:
    """测试未授权访问装备栏。"""
    response = await client.get("/api/v1/player/equipment")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_equipment_stats_empty(
    client: AsyncClient, test_player, player_token: str
) -> None:
    """测试查询空装备的属性加成。"""
    response = await client.get(
        "/api/v1/player/equipment/stats",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["stats"] == {}


@pytest.mark.asyncio
async def test_equip_item_success(
    client: AsyncClient, test_player, ops_token: str, player_token: str
) -> None:
    """测试装备物品成功。"""
    player_id = "00000000-0000-0000-0000-000000000001"
    add_response = await client.post(
        f"/api/v1/ops/players/{player_id}/inventory",
        json={
            "item_key": "item_iron_sword_01",
            "item_type": "equipment",
            "quantity": 1,
            "metadata_jsonb": {"name": "铁剑", "attack": 15},
        },
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "add-equip-001",
            "X-Trace-Id": "trace_test_equip",
        },
    )
    assert add_response.status_code == 201

    equip_response = await client.post(
        "/api/v1/player/equipment/equip",
        json={
            "item_key": "item_iron_sword_01",
            "slot": "weapon",
            "item_stats": {"attack": 15},
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "equip-001",
            "X-Trace-Id": "trace_test_equip",
        },
    )
    assert equip_response.status_code == 200
    data = equip_response.json()
    assert data["data"]["item_key"] == "item_iron_sword_01"
    assert data["data"]["slot"] == "weapon"
    assert data["data"]["stats"] == {"attack": 15}


@pytest.mark.asyncio
async def test_equip_item_not_in_inventory(
    client: AsyncClient, test_player, player_token: str
) -> None:
    """测试装备背包中没有的物品。"""
    response = await client.post(
        "/api/v1/player/equipment/equip",
        json={
            "item_key": "item_nonexistent",
            "slot": "weapon",
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "equip-nonexistent",
            "X-Trace-Id": "trace_test_equip_nonexistent",
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.ITEM_NOT_FOUND


@pytest.mark.asyncio
async def test_equip_item_slot_occupied(
    client: AsyncClient, test_player, ops_token: str, player_token: str
) -> None:
    """测试装备槽位已被占用。"""
    player_id = "00000000-0000-0000-0000-000000000001"

    add_response1 = await client.post(
        f"/api/v1/ops/players/{player_id}/inventory",
        json={
            "item_key": "item_iron_sword_01",
            "item_type": "equipment",
            "quantity": 1,
        },
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "add-sword-001",
            "X-Trace-Id": "trace_test_equip",
        },
    )
    assert add_response1.status_code == 201

    add_response2 = await client.post(
        f"/api/v1/ops/players/{player_id}/inventory",
        json={
            "item_key": "item_steel_sword_01",
            "item_type": "equipment",
            "quantity": 1,
        },
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "add-sword-002",
            "X-Trace-Id": "trace_test_equip",
        },
    )
    assert add_response2.status_code == 201

    equip_response1 = await client.post(
        "/api/v1/player/equipment/equip",
        json={
            "item_key": "item_iron_sword_01",
            "slot": "weapon",
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "equip-001",
            "X-Trace-Id": "trace_test_equip",
        },
    )
    assert equip_response1.status_code == 200

    equip_response2 = await client.post(
        "/api/v1/player/equipment/equip",
        json={
            "item_key": "item_steel_sword_01",
            "slot": "weapon",
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "equip-002",
            "X-Trace-Id": "trace_test_equip",
        },
    )
    assert equip_response2.status_code == 409
    data = equip_response2.json()
    assert data["code"] == PlayerErrorCodes.EQUIPMENT_SLOT_OCCUPIED


@pytest.mark.asyncio
async def test_unequip_item_success(
    client: AsyncClient, test_player, ops_token: str, player_token: str
) -> None:
    """测试卸下装备成功。"""
    player_id = "00000000-0000-0000-0000-000000000001"

    add_response = await client.post(
        f"/api/v1/ops/players/{player_id}/inventory",
        json={
            "item_key": "item_iron_sword_01",
            "item_type": "equipment",
            "quantity": 1,
        },
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "add-unequip-001",
            "X-Trace-Id": "trace_test_unequip",
        },
    )
    assert add_response.status_code == 201

    equip_response = await client.post(
        "/api/v1/player/equipment/equip",
        json={
            "item_key": "item_iron_sword_01",
            "slot": "weapon",
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "equip-unequip-001",
            "X-Trace-Id": "trace_test_unequip",
        },
    )
    assert equip_response.status_code == 200

    unequip_response = await client.post(
        "/api/v1/player/equipment/unequip",
        json={
            "slot": "weapon",
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "unequip-001",
            "X-Trace-Id": "trace_test_unequip",
        },
    )
    assert unequip_response.status_code == 200
    data = unequip_response.json()
    assert data["data"]["item_key"] == "item_iron_sword_01"
    assert data["data"]["slot"] == "weapon"

    inv_response = await client.get(
        "/api/v1/player/inventory",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert inv_response.status_code == 200
    inv_data = inv_response.json()
    assert len(inv_data["data"]) == 1
    assert inv_data["data"][0]["item_key"] == "item_iron_sword_01"
    assert inv_data["data"][0]["quantity"] == 1


@pytest.mark.asyncio
async def test_unequip_empty_slot(
    client: AsyncClient, test_player, player_token: str
) -> None:
    """测试卸下空槽位的装备。"""
    response = await client.post(
        "/api/v1/player/equipment/unequip",
        json={
            "slot": "weapon",
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "unequip-empty-001",
            "X-Trace-Id": "trace_test_unequip_empty",
        },
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == PlayerErrorCodes.CANNOT_UNEQUIP_EMPTY_SLOT


@pytest.mark.asyncio
async def test_equip_invalid_slot(
    client: AsyncClient, test_player, player_token: str
) -> None:
    """测试装备无效槽位。"""
    response = await client.post(
        "/api/v1/player/equipment/equip",
        json={
            "item_key": "item_test_01",
            "slot": "invalid_slot",
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "equip-invalid-slot",
            "X-Trace-Id": "trace_test_invalid_slot",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_equipment_with_stats(
    client: AsyncClient, test_player, ops_token: str, player_token: str
) -> None:
    """测试装备属性加成计算。"""
    player_id = "00000000-0000-0000-0000-000000000001"

    add_response1 = await client.post(
        f"/api/v1/ops/players/{player_id}/inventory",
        json={
            "item_key": "item_iron_sword_01",
            "item_type": "equipment",
            "quantity": 1,
        },
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "add-stats-sword",
            "X-Trace-Id": "trace_test_stats",
        },
    )
    assert add_response1.status_code == 201

    add_response2 = await client.post(
        f"/api/v1/ops/players/{player_id}/inventory",
        json={
            "item_key": "item_iron_helmet_01",
            "item_type": "equipment",
            "quantity": 1,
        },
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "add-stats-helmet",
            "X-Trace-Id": "trace_test_stats",
        },
    )
    assert add_response2.status_code == 201

    equip_response1 = await client.post(
        "/api/v1/player/equipment/equip",
        json={
            "item_key": "item_iron_sword_01",
            "slot": "weapon",
            "item_stats": {"attack": 15, "strength": 5},
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "equip-stats-sword",
            "X-Trace-Id": "trace_test_stats",
        },
    )
    assert equip_response1.status_code == 200

    equip_response2 = await client.post(
        "/api/v1/player/equipment/equip",
        json={
            "item_key": "item_iron_helmet_01",
            "slot": "head",
            "item_stats": {"defense": 10, "strength": 3},
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "equip-stats-helmet",
            "X-Trace-Id": "trace_test_stats",
        },
    )
    assert equip_response2.status_code == 200

    stats_response = await client.get(
        "/api/v1/player/equipment/stats",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert stats_response.status_code == 200
    stats_data = stats_response.json()
    assert stats_data["data"]["stats"]["attack"] == 15
    assert stats_data["data"]["stats"]["defense"] == 10
    assert stats_data["data"]["stats"]["strength"] == 8
