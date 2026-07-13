"""装备定义 API 测试。"""

import pytest
from httpx import AsyncClient

from app.core.errors import WorldErrorCodes


@pytest.mark.asyncio
async def test_list_items_empty(client: AsyncClient, player_token: str):
    """测试查询空物品列表。"""
    response = await client.get(
        "/api/v1/world/items",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert data["data"]["items"] == []
    assert data["data"]["total"] == 0


@pytest.mark.asyncio
async def test_list_items_unauthorized(client: AsyncClient):
    """测试未授权查询物品列表。"""
    response = await client.get("/api/v1/world/items")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_item_success(client: AsyncClient, ops_token: str):
    """测试运营创建物品成功。"""
    response = await client.post(
        "/api/v1/ops/world/items",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-item-001",
            "X-Trace-Id": "trace_create_item_001",
        },
        json={
            "item_key": "item_iron_sword_01",
            "item_type": "weapon",
            "item_slot": "weapon",
            "name": "铁剑",
            "description": "一把普通的铁剑",
            "rarity": "common",
            "chapter_id": "ch_01",
            "level_requirement": 1,
            "stats": {"attack": 10, "strength": 2},
            "effects": {"critical_chance": 0.05},
            "sell_price": 50,
            "stackable": False,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "item_id" in data["data"]
    assert data["data"]["item_key"] == "item_iron_sword_01"
    assert data["data"]["item_type"] == "weapon"
    assert data["data"]["item_slot"] == "weapon"
    assert data["data"]["name"] == "铁剑"
    assert data["data"]["rarity"] == "common"
    assert data["data"]["stats"] == {"attack": 10, "strength": 2}
    assert data["data"]["effects"] == {"critical_chance": 0.05}
    assert data["data"]["sell_price"] == 50
    assert data["trace_id"] == "trace_create_item_001"


@pytest.mark.asyncio
async def test_create_item_no_token_returns_401(client: AsyncClient):
    """测试未授权创建物品。"""
    response = await client.post(
        "/api/v1/ops/world/items",
        json={
            "item_key": "item_test_01",
            "item_type": "weapon",
            "name": "测试物品",
            "rarity": "common",
            "chapter_id": "ch_01",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_item_player_role_forbidden(
    client: AsyncClient, player_token: str
):
    """测试玩家角色创建物品（权限不足）。"""
    response = await client.post(
        "/api/v1/ops/world/items",
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "test-create-item-002",
        },
        json={
            "item_key": "item_test_01",
            "item_type": "weapon",
            "name": "测试物品",
            "rarity": "common",
            "chapter_id": "ch_01",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_item_duplicate_key(
    client: AsyncClient, ops_token: str
):
    """测试创建重复 item_key 的物品。"""
    response1 = await client.post(
        "/api/v1/ops/world/items",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-dup-001",
        },
        json={
            "item_key": "item_duplicate_01",
            "item_type": "weapon",
            "item_slot": "weapon",
            "name": "重复物品",
            "rarity": "common",
            "chapter_id": "ch_01",
        },
    )
    assert response1.status_code == 201

    response2 = await client.post(
        "/api/v1/ops/world/items",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-dup-002",
        },
        json={
            "item_key": "item_duplicate_01",
            "item_type": "weapon",
            "item_slot": "weapon",
            "name": "重复物品2",
            "rarity": "rare",
            "chapter_id": "ch_01",
        },
    )
    assert response2.status_code == 409
    data = response2.json()
    assert data["code"] == WorldErrorCodes.ITEM_KEY_EXISTS


@pytest.mark.asyncio
async def test_create_item_invalid_type(client: AsyncClient, ops_token: str):
    """测试创建物品时使用无效的物品类型。"""
    response = await client.post(
        "/api/v1/ops/world/items",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-invalid-type-001",
        },
        json={
            "item_key": "item_invalid_01",
            "item_type": "invalid_type",
            "name": "无效类型物品",
            "rarity": "common",
            "chapter_id": "ch_01",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_item_by_key_success(client: AsyncClient, ops_token: str):
    """测试根据 item_key 查询物品。"""
    create_response = await client.post(
        "/api/v1/ops/world/items",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-get-item-001",
        },
        json={
            "item_key": "item_get_test_01",
            "item_type": "armor",
            "item_slot": "chest",
            "name": "铁甲",
            "rarity": "uncommon",
            "chapter_id": "ch_01",
            "stats": {"defense": 20},
        },
    )
    assert create_response.status_code == 201

    get_response = await client.get(
        "/api/v1/world/items/item_get_test_01",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["data"]["item_key"] == "item_get_test_01"
    assert data["data"]["item_type"] == "armor"
    assert data["data"]["item_slot"] == "chest"
    assert data["data"]["stats"] == {"defense": 20}


@pytest.mark.asyncio
async def test_get_item_not_found(client: AsyncClient, player_token: str):
    """测试查询不存在的物品。"""
    response = await client.get(
        "/api/v1/world/items/item_nonexistent_999",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == WorldErrorCodes.ITEM_NOT_FOUND


@pytest.mark.asyncio
async def test_list_items_with_filters(
    client: AsyncClient, ops_token: str
):
    """测试带过滤器查询物品列表。"""
    items = [
        {"item_key": "item_sword_01", "item_type": "weapon", "item_slot": "weapon", "name": "铁剑", "rarity": "common", "chapter_id": "ch_01"},
        {"item_key": "item_sword_02", "item_type": "weapon", "item_slot": "weapon", "name": "钢剑", "rarity": "rare", "chapter_id": "ch_01"},
        {"item_key": "item_armor_01", "item_type": "armor", "item_slot": "chest", "name": "铁甲", "rarity": "common", "chapter_id": "ch_01"},
        {"item_key": "item_potion_01", "item_type": "consumable", "name": "治疗药水", "rarity": "common", "chapter_id": "ch_02"},
    ]

    for i, item in enumerate(items):
        response = await client.post(
            "/api/v1/ops/world/items",
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": f"test-filter-{i}",
            },
            json=item,
        )
        assert response.status_code == 201

    weapon_response = await client.get(
        "/api/v1/world/items?item_type=weapon",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert weapon_response.status_code == 200
    weapon_data = weapon_response.json()
    assert weapon_data["data"]["total"] == 2

    rare_response = await client.get(
        "/api/v1/world/items?rarity=rare",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert rare_response.status_code == 200
    rare_data = rare_response.json()
    assert rare_data["data"]["total"] == 1

    ch01_response = await client.get(
        "/api/v1/world/items?chapter_id=ch_01",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert ch01_response.status_code == 200
    ch01_data = ch01_response.json()
    assert ch01_data["data"]["total"] == 3


@pytest.mark.asyncio
async def test_update_item_success(client: AsyncClient, ops_token: str):
    """测试更新物品成功。"""
    create_response = await client.post(
        "/api/v1/ops/world/items",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-update-001",
        },
        json={
            "item_key": "item_update_test_01",
            "item_type": "weapon",
            "item_slot": "weapon",
            "name": "旧名字",
            "rarity": "common",
            "chapter_id": "ch_01",
            "sell_price": 10,
        },
    )
    assert create_response.status_code == 201
    item_id = create_response.json()["data"]["item_id"]

    update_response = await client.put(
        f"/api/v1/ops/world/items/{item_id}",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-update-002",
        },
        json={
            "name": "新名字",
            "sell_price": 100,
            "stats": {"attack": 25},
        },
    )
    assert update_response.status_code == 200
    update_data = update_response.json()
    assert update_data["data"]["name"] == "新名字"
    assert update_data["data"]["sell_price"] == 100
    assert update_data["data"]["stats"] == {"attack": 25}


@pytest.mark.asyncio
async def test_delete_item_success(client: AsyncClient, ops_token: str):
    """测试删除物品成功。"""
    create_response = await client.post(
        "/api/v1/ops/world/items",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-delete-001",
        },
        json={
            "item_key": "item_delete_test_01",
            "item_type": "material",
            "name": "可删除物品",
            "rarity": "common",
            "chapter_id": "ch_01",
        },
    )
    assert create_response.status_code == 201
    item_id = create_response.json()["data"]["item_id"]

    delete_response = await client.delete(
        f"/api/v1/ops/world/items/{item_id}",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-delete-002",
        },
    )
    assert delete_response.status_code == 200
    delete_data = delete_response.json()
    assert delete_data["data"]["success"] is True
    assert delete_data["data"]["item_id"] == str(item_id)

    get_response = await client.get(
        "/api/v1/world/items/item_delete_test_01",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert get_response.status_code == 404
