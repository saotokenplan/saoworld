"""背包 API 测试。"""

import pytest
from httpx import AsyncClient

from app.core.errors import PlayerErrorCodes


@pytest.mark.asyncio
async def test_get_player_inventory_empty(
    client: AsyncClient, test_player, player_token: str
) -> None:
    """测试查询空背包。"""
    response = await client.get(
        "/api/v1/player/inventory",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert data["data"] == []


@pytest.mark.asyncio
async def test_get_player_inventory_with_items(
    client: AsyncClient, test_inventory_item, player_token: str
) -> None:
    """测试查询有物品的背包。"""
    response = await client.get(
        "/api/v1/player/inventory",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    item = data["data"][0]
    assert item["item_key"] == "item_health_potion_01"
    assert item["item_type"] == "consumable"
    assert item["quantity"] == 5


@pytest.mark.asyncio
async def test_get_inventory_unauthorized(client: AsyncClient) -> None:
    """测试未授权访问背包。"""
    response = await client.get("/api/v1/player/inventory")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_use_inventory_item_success(
    client: AsyncClient, test_inventory_item, player_token: str
) -> None:
    """测试使用消耗品成功。"""
    response = await client.post(
        "/api/v1/player/inventory/use?item_key=item_health_potion_01",
        json={"quantity": 2},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["quantity"] == 3


@pytest.mark.asyncio
async def test_use_inventory_item_not_found(
    client: AsyncClient, test_player, player_token: str
) -> None:
    """测试使用不存在的物品。"""
    response = await client.post(
        "/api/v1/player/inventory/use?item_key=item_nonexistent",
        json={"quantity": 1},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.ITEM_NOT_FOUND


@pytest.mark.asyncio
async def test_use_inventory_item_insufficient_quantity(
    client: AsyncClient, test_inventory_item, player_token: str
) -> None:
    """测试使用数量不足的物品。"""
    response = await client.post(
        "/api/v1/player/inventory/use?item_key=item_health_potion_01",
        json={"quantity": 10},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == PlayerErrorCodes.INSUFFICIENT_QUANTITY


@pytest.mark.asyncio
async def test_use_non_consumable_item(
    client: AsyncClient, test_player, ops_token: str, player_token: str
) -> None:
    """测试使用非消耗品物品。"""
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
            "Idempotency-Key": "add-equipment-001",
            "X-Trace-Id": "trace_test_equip",
        },
    )
    assert add_response.status_code == 201

    response = await client.post(
        "/api/v1/player/inventory/use?item_key=item_iron_sword_01",
        json={"quantity": 1},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == PlayerErrorCodes.INVALID_ITEM_TYPE


@pytest.mark.asyncio
async def test_ops_add_inventory_item(
    client: AsyncClient, test_player, ops_token: str
) -> None:
    """测试运营添加物品。"""
    player_id = "00000000-0000-0000-0000-000000000001"
    response = await client.post(
        f"/api/v1/ops/players/{player_id}/inventory",
        json={
            "item_key": "item_iron_ore_01",
            "item_type": "material",
            "quantity": 10,
            "metadata_jsonb": {"name": "铁矿石"},
        },
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "add-item-001",
            "X-Trace-Id": "trace_test_add",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["item_key"] == "item_iron_ore_01"
    assert data["data"]["quantity"] == 10
    assert data["data"]["item_type"] == "material"


@pytest.mark.asyncio
async def test_ops_add_item_stacking(
    client: AsyncClient, test_inventory_item, ops_token: str
) -> None:
    """测试运营添加已存在物品（数量叠加）。"""
    player_id = "00000000-0000-0000-0000-000000000001"
    response = await client.post(
        f"/api/v1/ops/players/{player_id}/inventory",
        json={
            "item_key": "item_health_potion_01",
            "item_type": "consumable",
            "quantity": 3,
        },
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "add-item-stack-001",
            "X-Trace-Id": "trace_test_stack",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["quantity"] == 8  # 5 + 3


@pytest.mark.asyncio
async def test_ops_remove_inventory_item(
    client: AsyncClient, test_inventory_item, ops_token: str
) -> None:
    """测试运营移除物品。"""
    player_id = "00000000-0000-0000-0000-000000000001"
    response = await client.request(
        "DELETE",
        f"/api/v1/ops/players/{player_id}/inventory/item_health_potion_01",
        json={"quantity": 2},
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "remove-item-001",
            "X-Trace-Id": "trace_test_remove",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["quantity"] == 3  # 5 - 2


@pytest.mark.asyncio
async def test_ops_remove_item_insufficient_quantity(
    client: AsyncClient, test_inventory_item, ops_token: str
) -> None:
    """测试运营移除数量不足的物品。"""
    player_id = "00000000-0000-0000-0000-000000000001"
    response = await client.request(
        "DELETE",
        f"/api/v1/ops/players/{player_id}/inventory/item_health_potion_01",
        json={"quantity": 10},
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "remove-item-insufficient-001",
            "X-Trace-Id": "trace_test_remove_insuf",
        },
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == PlayerErrorCodes.INSUFFICIENT_QUANTITY


@pytest.mark.asyncio
async def test_ops_inventory_player_not_found(
    client: AsyncClient, ops_token: str
) -> None:
    """测试运营为不存在的玩家添加物品。"""
    fake_player_id = "00000000-0000-0000-0000-999999999999"
    response = await client.post(
        f"/api/v1/ops/players/{fake_player_id}/inventory",
        json={
            "item_key": "item_test_01",
            "item_type": "material",
            "quantity": 1,
        },
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "add-item-notfound-001",
            "X-Trace-Id": "trace_test_notfound",
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.PLAYER_NOT_FOUND


@pytest.mark.asyncio
async def test_inventory_envelope_format(
    client: AsyncClient, test_inventory_item, player_token: str
) -> None:
    """测试背包接口 envelope 格式。"""
    response = await client.get(
        "/api/v1/player/inventory",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert "meta" in data
    assert "total" in data["meta"]
