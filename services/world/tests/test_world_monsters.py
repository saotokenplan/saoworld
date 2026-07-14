"""怪物定义 API 测试。"""

import pytest
from httpx import AsyncClient

from app.core.errors import WorldErrorCodes


@pytest.mark.asyncio
async def test_list_monsters_empty(client: AsyncClient, player_token: str):
    """测试查询空怪物列表。"""
    response = await client.get(
        "/api/v1/world/monsters",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert data["data"]["monsters"] == []
    assert data["data"]["total"] == 0


@pytest.mark.asyncio
async def test_list_monsters_unauthorized(client: AsyncClient):
    """测试未授权查询怪物列表。"""
    response = await client.get("/api/v1/world/monsters")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_monster_success(client: AsyncClient, ops_token: str):
    """测试运营创建怪物成功。"""
    response = await client.post(
        "/api/v1/ops/world/monsters",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-monster-001",
            "X-Trace-Id": "trace_create_monster_001",
        },
        json={
            "monster_key": "monster_wasteland_wolf",
            "name": "荒原狼",
            "monster_type": "beast",
            "chapter_id": "chapter_02",
            "region_key": "region_wasteland_01",
            "level": 5,
            "hp": 120,
            "attack": 15,
            "defense": 5,
            "speed": 8,
            "description": "荒原上成群出没的灰狼，比普通狼更凶猛。",
            "behavior_pattern": {
                "aggression": "aggressive",
                "attack_pattern": "melee",
                "special_behaviors": ["pack_hunt"],
            },
            "loot_table": [
                {"item_key": "item_wolf_pelt", "drop_rate": 0.6, "quantity_min": 1, "quantity_max": 2},
            ],
            "skills": [
                {"skill_key": "skill_bite", "name": "撕咬", "damage_multiplier": 1.2, "cooldown": 0},
            ],
            "min_reputation": 0,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "monster_id" in data["data"]
    assert data["data"]["monster_key"] == "monster_wasteland_wolf"
    assert data["data"]["monster_type"] == "beast"
    assert data["data"]["name"] == "荒原狼"
    assert data["trace_id"] == "trace_create_monster_001"


@pytest.mark.asyncio
async def test_create_monster_no_token_returns_401(client: AsyncClient):
    """测试未授权创建怪物。"""
    response = await client.post(
        "/api/v1/ops/world/monsters",
        json={
            "monster_key": "monster_test_01",
            "name": "测试怪物",
            "monster_type": "beast",
            "chapter_id": "chapter_01",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_monster_player_role_forbidden(
    client: AsyncClient, player_token: str
):
    """测试玩家角色创建怪物（权限不足）。"""
    response = await client.post(
        "/api/v1/ops/world/monsters",
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "test-create-monster-002",
        },
        json={
            "monster_key": "monster_test_01",
            "name": "测试怪物",
            "monster_type": "beast",
            "chapter_id": "chapter_01",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_monster_duplicate_key(
    client: AsyncClient, ops_token: str
):
    """测试创建重复 monster_key 的怪物。"""
    response1 = await client.post(
        "/api/v1/ops/world/monsters",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-monster-dup-001",
        },
        json={
            "monster_key": "monster_duplicate_01",
            "name": "重复怪物",
            "monster_type": "beast",
            "chapter_id": "chapter_01",
        },
    )
    assert response1.status_code == 201

    response2 = await client.post(
        "/api/v1/ops/world/monsters",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-monster-dup-002",
        },
        json={
            "monster_key": "monster_duplicate_01",
            "name": "重复怪物2",
            "monster_type": "humanoid",
            "chapter_id": "chapter_01",
        },
    )
    assert response2.status_code == 409
    data = response2.json()
    assert data["code"] == WorldErrorCodes.MONSTER_KEY_EXISTS


@pytest.mark.asyncio
async def test_create_monster_invalid_type(client: AsyncClient, ops_token: str):
    """测试创建怪物时使用无效的怪物类型。"""
    response = await client.post(
        "/api/v1/ops/world/monsters",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-monster-invalid-type-001",
        },
        json={
            "monster_key": "monster_invalid_01",
            "name": "无效类型怪物",
            "monster_type": "invalid_type",
            "chapter_id": "chapter_01",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_monster_by_id_success(client: AsyncClient, ops_token: str, player_token: str):
    """测试根据 ID 查询怪物详情。"""
    create_response = await client.post(
        "/api/v1/ops/world/monsters",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-get-monster-001",
        },
        json={
            "monster_key": "monster_get_test_01",
            "name": "骷髅战士",
            "monster_type": "undead",
            "chapter_id": "chapter_01",
            "region_key": "region_crypt_01",
            "level": 10,
            "hp": 200,
            "attack": 25,
            "defense": 10,
            "speed": 4,
        },
    )
    assert create_response.status_code == 201
    monster_id = create_response.json()["data"]["monster_id"]

    get_response = await client.get(
        f"/api/v1/world/monsters/{monster_id}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["data"]["monster_key"] == "monster_get_test_01"
    assert data["data"]["monster_type"] == "undead"
    assert data["data"]["level"] == 10


@pytest.mark.asyncio
async def test_get_monster_not_found(client: AsyncClient, player_token: str):
    """测试查询不存在的怪物。"""
    fake_id = "00000000-0000-0000-0000-000000000999"
    response = await client.get(
        f"/api/v1/world/monsters/{fake_id}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == WorldErrorCodes.MONSTER_NOT_FOUND


@pytest.mark.asyncio
async def test_list_monsters_with_filters(
    client: AsyncClient, ops_token: str, player_token: str
):
    """测试带过滤器查询怪物列表。"""
    monsters = [
        {
            "monster_key": "monster_wolf_01",
            "name": "荒原狼",
            "monster_type": "beast",
            "chapter_id": "chapter_01",
            "region_key": "region_wasteland_01",
            "level": 5,
            "hp": 80,
            "attack": 12,
            "defense": 3,
            "speed": 8,
        },
        {
            "monster_key": "monster_skeleton_01",
            "name": "骷髅兵",
            "monster_type": "undead",
            "chapter_id": "chapter_01",
            "region_key": "region_crypt_01",
            "level": 8,
            "hp": 150,
            "attack": 20,
            "defense": 8,
            "speed": 3,
        },
        {
            "monster_key": "monster_goblin_01",
            "name": "哥布林",
            "monster_type": "humanoid",
            "chapter_id": "chapter_02",
            "region_key": "region_cave_01",
            "level": 3,
            "hp": 40,
            "attack": 8,
            "defense": 2,
            "speed": 6,
        },
    ]

    for i, monster in enumerate(monsters):
        response = await client.post(
            "/api/v1/ops/world/monsters",
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": f"test-monster-filter-{i}",
            },
            json=monster,
        )
        assert response.status_code == 201

    beast_response = await client.get(
        "/api/v1/world/monsters?monster_type=beast",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert beast_response.status_code == 200
    beast_data = beast_response.json()
    assert beast_data["data"]["total"] == 1

    ch01_response = await client.get(
        "/api/v1/world/monsters?chapter_id=chapter_01",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert ch01_response.status_code == 200
    ch01_data = ch01_response.json()
    assert ch01_data["data"]["total"] == 2

    region_response = await client.get(
        "/api/v1/world/monsters?region_key=region_crypt_01",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert region_response.status_code == 200
    region_data = region_response.json()
    assert region_data["data"]["total"] == 1


@pytest.mark.asyncio
async def test_create_monster_boss_type(client: AsyncClient, ops_token: str):
    """测试创建 Boss 类型怪物。"""
    response = await client.post(
        "/api/v1/ops/world/monsters",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-boss-001",
            "X-Trace-Id": "trace_create_boss_001",
        },
        json={
            "monster_key": "monster_boss_lich_king",
            "name": "巫妖王",
            "monster_type": "boss",
            "chapter_id": "chapter_02",
            "region_key": "region_dark_tower_01",
            "level": 30,
            "hp": 5000,
            "attack": 80,
            "defense": 30,
            "speed": 6,
            "description": "黑暗之塔的主人，拥有强大亡灵魔力的古老巫妖。",
            "behavior_pattern": {
                "aggression": "aggressive",
                "attack_pattern": "magic",
                "special_behaviors": ["phase_transition", "summon_minions"],
                "phases": [
                    {"phase_name": "Phase 1", "hp_threshold": 0.7, "new_skills": ["dark_bolt"], "behavior_change": "More aggressive"},
                    {"phase_name": "Phase 2", "hp_threshold": 0.3, "new_skills": ["death_grip", "soul_drain"], "behavior_change": "Berserk"},
                ],
            },
            "loot_table": [
                {"item_key": "item_lich_crown", "drop_rate": 0.1, "quantity_min": 1, "quantity_max": 1},
                {"item_key": "item_dark_orb", "drop_rate": 0.5, "quantity_min": 1, "quantity_max": 3},
            ],
            "skills": [
                {"skill_key": "skill_dark_bolt", "name": "暗影弹", "damage_multiplier": 2.0, "cooldown": 3, "skill_type": "active"},
                {"skill_key": "skill_death_grip", "name": "死亡之握", "damage_multiplier": 3.0, "cooldown": 10, "skill_type": "active"},
                {"skill_key": "skill_soul_drain", "name": "灵魂虹吸", "damage_multiplier": 4.0, "cooldown": 15, "skill_type": "ultimate"},
            ],
            "min_reputation": 50,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["monster_type"] == "boss"
    assert data["data"]["name"] == "巫妖王"
    assert data["trace_id"] == "trace_create_boss_001"


@pytest.mark.asyncio
async def test_create_monster_minimal_fields(client: AsyncClient, ops_token: str):
    """测试仅提供必填字段创建怪物。"""
    response = await client.post(
        "/api/v1/ops/world/monsters",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-monster-minimal-001",
        },
        json={
            "monster_key": "monster_slime_01",
            "name": "史莱姆",
            "monster_type": "elemental",
            "chapter_id": "chapter_01",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["monster_key"] == "monster_slime_01"
    assert data["data"]["monster_type"] == "elemental"
    assert data["data"]["name"] == "史莱姆"


@pytest.mark.asyncio
async def test_create_monster_invalid_level(client: AsyncClient, ops_token: str):
    """测试创建怪物时等级超出范围。"""
    response = await client.post(
        "/api/v1/ops/world/monsters",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-monster-level-001",
        },
        json={
            "monster_key": "monster_overlevel",
            "name": "超等级怪物",
            "monster_type": "beast",
            "chapter_id": "chapter_01",
            "level": 100,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_monster_negative_hp(client: AsyncClient, ops_token: str):
    """测试创建怪物时 HP 为负数。"""
    response = await client.post(
        "/api/v1/ops/world/monsters",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-monster-hp-001",
        },
        json={
            "monster_key": "monster_neg_hp",
            "name": "负血量怪物",
            "monster_type": "beast",
            "chapter_id": "chapter_01",
            "hp": -10,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_boss_success(client: AsyncClient, ops_token: str):
    """测试创建 Boss 成功。"""
    response = await client.post(
        "/api/v1/ops/world/monsters/bosses",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-boss-api-001",
            "X-Trace-Id": "trace_create_boss_api_001",
        },
        json={
            "monster_key": "boss_ancient_tree",
            "name": "古树守护者",
            "chapter_id": "chapter_02",
            "region_key": "region_forest_01",
            "level": 12,
            "hp": 800,
            "attack": 28,
            "defense": 15,
            "speed": 3,
            "description": "幽光森林深处的千年古树，被自然之力赋予了意识。",
            "behavior_pattern": {
                "aggression": "aggressive",
                "attack_pattern": "magic",
                "special_behaviors": ["enrage", "phase_change"],
            },
            "loot_table": [
                {"item_key": "item_ancient_core", "drop_rate": 1.0, "quantity_min": 1, "quantity_max": 1},
            ],
            "skills": [
                {"skill_key": "skill_root_strike", "name": "根系打击", "damage_multiplier": 1.0, "cooldown": 0},
            ],
            "boss_rank": "legendary",
            "phase_count": 3,
            "special_skills": [
                {"skill_key": "skill_root_bind", "name": "根系缠绕", "description": "束缚玩家", "cooldown": 8},
                {"skill_key": "skill_nature_force", "name": "自然之力", "description": "恢复生命", "cooldown": 15},
            ],
            "enrage_threshold": 0.3,
            "reward": {
                "experience": 5000,
                "items": [{"item_key": "item_ancient_core", "quantity": 1}],
            },
            "min_reputation": 0,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["monster_key"] == "boss_ancient_tree"
    assert data["data"]["monster_type"] == "boss"
    assert data["trace_id"] == "trace_create_boss_api_001"


@pytest.mark.asyncio
async def test_create_boss_duplicate_key(client: AsyncClient, ops_token: str):
    """测试创建重复 monster_key 的 Boss。"""
    await client.post(
        "/api/v1/ops/world/monsters/bosses",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-boss-dup-001",
        },
        json={
            "monster_key": "boss_duplicate_test",
            "name": "重复Boss",
            "chapter_id": "chapter_02",
            "region_key": "region_forest_01",
            "level": 10,
            "hp": 500,
            "attack": 25,
            "defense": 10,
            "speed": 4,
            "boss_rank": "legendary",
            "phase_count": 2,
            "special_skills": [],
            "enrage_threshold": 0.3,
            "reward": {"experience": 3000, "items": []},
        },
    )

    response = await client.post(
        "/api/v1/ops/world/monsters/bosses",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-boss-dup-002",
        },
        json={
            "monster_key": "boss_duplicate_test",
            "name": "重复Boss2",
            "chapter_id": "chapter_02",
            "region_key": "region_oasis_01",
            "level": 15,
            "hp": 1000,
            "attack": 35,
            "defense": 15,
            "speed": 5,
            "boss_rank": "mythic",
            "phase_count": 3,
            "special_skills": [],
            "enrage_threshold": 0.25,
            "reward": {"experience": 6000, "items": []},
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_bosses(client: AsyncClient, ops_token: str, player_token: str):
    """测试查询 Boss 列表。"""
    await client.post(
        "/api/v1/ops/world/monsters/bosses",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-boss-list-001",
        },
        json={
            "monster_key": "boss_list_test_01",
            "name": "测试Boss1",
            "chapter_id": "chapter_02",
            "region_key": "region_forest_01",
            "level": 10,
            "hp": 500,
            "attack": 25,
            "defense": 10,
            "speed": 4,
            "boss_rank": "legendary",
            "phase_count": 2,
            "special_skills": [],
            "enrage_threshold": 0.3,
            "reward": {"experience": 3000, "items": []},
        },
    )

    await client.post(
        "/api/v1/ops/world/monsters/bosses",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-boss-list-002",
        },
        json={
            "monster_key": "boss_list_test_02",
            "name": "测试Boss2",
            "chapter_id": "chapter_02",
            "region_key": "region_oasis_01",
            "level": 15,
            "hp": 1000,
            "attack": 35,
            "defense": 15,
            "speed": 5,
            "boss_rank": "mythic",
            "phase_count": 3,
            "special_skills": [],
            "enrage_threshold": 0.25,
            "reward": {"experience": 6000, "items": []},
        },
    )

    response = await client.get(
        "/api/v1/world/bosses",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "bosses" in data["data"]
    assert data["data"]["total"] >= 2


@pytest.mark.asyncio
async def test_list_bosses_filter_by_region(client: AsyncClient, ops_token: str, player_token: str):
    """测试按区域筛选 Boss 列表。"""
    await client.post(
        "/api/v1/ops/world/monsters/bosses",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-boss-region-001",
        },
        json={
            "monster_key": "boss_region_test_01",
            "name": "森林Boss",
            "chapter_id": "chapter_02",
            "region_key": "region_forest_01",
            "level": 10,
            "hp": 500,
            "attack": 25,
            "defense": 10,
            "speed": 4,
            "boss_rank": "legendary",
            "phase_count": 2,
            "special_skills": [],
            "enrage_threshold": 0.3,
            "reward": {"experience": 3000, "items": []},
        },
    )

    response = await client.get(
        "/api/v1/world/bosses?region_key=region_forest_01",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] >= 1


@pytest.mark.asyncio
async def test_get_boss_by_key(client: AsyncClient, ops_token: str, player_token: str):
    """测试按 monster_key 查询 Boss 详情。"""
    await client.post(
        "/api/v1/ops/world/monsters/bosses",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-get-boss-001",
        },
        json={
            "monster_key": "boss_get_test_01",
            "name": "古树守护者",
            "chapter_id": "chapter_02",
            "region_key": "region_forest_01",
            "level": 12,
            "hp": 800,
            "attack": 28,
            "defense": 15,
            "speed": 3,
            "boss_rank": "legendary",
            "phase_count": 3,
            "special_skills": [
                {"skill_key": "skill_root_bind", "name": "根系缠绕", "description": "束缚玩家", "cooldown": 8},
            ],
            "enrage_threshold": 0.3,
            "reward": {"experience": 5000, "items": []},
        },
    )

    response = await client.get(
        "/api/v1/world/bosses/boss_get_test_01",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["monster_key"] == "boss_get_test_01"
    assert data["data"]["name"] == "古树守护者"
    assert data["data"]["is_boss"] is True
    assert data["data"]["boss_rank"] == "legendary"
    assert data["data"]["phase_count"] == 3
    assert data["data"]["enrage_threshold"] == 0.3


@pytest.mark.asyncio
async def test_get_boss_not_found(client: AsyncClient, player_token: str):
    """测试查询不存在的 Boss。"""
    response = await client.get(
        "/api/v1/world/bosses/boss_not_exist",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == WorldErrorCodes.MONSTER_NOT_FOUND


@pytest.mark.asyncio
async def test_create_boss_invalid_rank(client: AsyncClient, ops_token: str):
    """测试创建 Boss 时使用无效的 boss_rank。"""
    response = await client.post(
        "/api/v1/ops/world/monsters/bosses",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-boss-invalid-rank-001",
        },
        json={
            "monster_key": "boss_invalid_rank",
            "name": "无效等级Boss",
            "chapter_id": "chapter_02",
            "region_key": "region_forest_01",
            "level": 10,
            "hp": 500,
            "attack": 25,
            "defense": 10,
            "speed": 4,
            "boss_rank": "invalid_rank",
            "phase_count": 2,
            "special_skills": [],
            "enrage_threshold": 0.3,
            "reward": {"experience": 3000, "items": []},
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_boss_invalid_enrage_threshold(client: AsyncClient, ops_token: str):
    """测试创建 Boss 时 enrage_threshold 超出范围。"""
    response = await client.post(
        "/api/v1/ops/world/monsters/bosses",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-boss-enrage-001",
        },
        json={
            "monster_key": "boss_invalid_enrage",
            "name": "无效狂暴Boss",
            "chapter_id": "chapter_02",
            "region_key": "region_forest_01",
            "level": 10,
            "hp": 500,
            "attack": 25,
            "defense": 10,
            "speed": 4,
            "boss_rank": "legendary",
            "phase_count": 2,
            "special_skills": [],
            "enrage_threshold": 1.5,
            "reward": {"experience": 3000, "items": []},
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_boss_player_forbidden(client: AsyncClient, player_token: str):
    """测试玩家角色创建 Boss（权限不足）。"""
    response = await client.post(
        "/api/v1/ops/world/monsters/bosses",
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "test-boss-player-001",
        },
        json={
            "monster_key": "boss_player_test",
            "name": "玩家创建的Boss",
            "chapter_id": "chapter_02",
            "region_key": "region_forest_01",
            "level": 10,
            "hp": 500,
            "attack": 25,
            "defense": 10,
            "speed": 4,
            "boss_rank": "legendary",
            "phase_count": 2,
            "special_skills": [],
            "enrage_threshold": 0.3,
            "reward": {"experience": 3000, "items": []},
        },
    )
    assert response.status_code == 403
