"""怪物数据适配器测试。"""

import pytest

from app.core.monster_data_adapter import MonsterDataAdapter


@pytest.fixture
def adapter() -> MonsterDataAdapter:
    return MonsterDataAdapter(chapter_id="chapter_01")


class TestMonsterDataAdapter:
    """MonsterDataAdapter 测试类。"""

    def test_adapt_complete_data(self, adapter: MonsterDataAdapter) -> None:
        """测试完整数据的适配。"""
        raw_data = {
            "monster_key": "wasteland_wolf",
            "name": "荒原狼",
            "monster_type": "beast",
            "chapter_id": "chapter_02",
            "region_key": "wasteland_01",
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
        }

        result = adapter.adapt(raw_data)

        assert result["monster_key"] == "monster_wasteland_wolf"
        assert result["name"] == "荒原狼"
        assert result["monster_type"] == "beast"
        assert result["chapter_id"] == "chapter_02"
        assert result["region_key"] == "region_wasteland_01"
        assert result["level"] == 5
        assert result["hp"] == 120
        assert result["attack"] == 15
        assert result["defense"] == 5
        assert result["speed"] == 8
        assert result["description"] == "荒原上成群出没的灰狼，比普通狼更凶猛。"
        assert result["behavior_pattern"]["aggression"] == "aggressive"
        assert len(result["loot_table"]) == 1
        assert len(result["skills"]) == 1

    def test_adapt_missing_fields(self, adapter: MonsterDataAdapter) -> None:
        """测试缺失字段时使用默认值。"""
        raw_data = {
            "name": "幽灵",
        }

        result = adapter.adapt(raw_data)

        assert result["monster_key"].startswith("monster_")
        assert result["name"] == "幽灵"
        assert result["monster_type"] == "beast"
        assert result["chapter_id"] == "chapter_01"
        assert result["level"] == 1
        assert result["hp"] == 10

    def test_adapt_normalizes_monster_key(self, adapter: MonsterDataAdapter) -> None:
        """测试怪物 key 规范化（添加 monster_ 前缀）。"""
        result = adapter.adapt({"monster_key": "goblin", "name": "Goblin"})
        assert result["monster_key"] == "monster_goblin"

    def test_adapt_normalizes_region_key(self, adapter: MonsterDataAdapter) -> None:
        """测试区域 key 规范化（添加 region_ 前缀）。"""
        result = adapter.adapt({"region_key": "wasteland", "name": "Test"})
        assert result["region_key"] == "region_wasteland"

    def test_adapt_invalid_monster_type_defaults_to_beast(self, adapter: MonsterDataAdapter) -> None:
        """测试无效怪物类型默认为 beast。"""
        result = adapter.adapt({"monster_type": "invalid_type", "name": "Test"})
        assert result["monster_type"] == "beast"

    def test_adapt_valid_monster_types(self, adapter: MonsterDataAdapter) -> None:
        """测试所有合法怪物类型。"""
        for monster_type in ["beast", "humanoid", "undead", "mechanical", "elemental", "demon", "dragon", "boss"]:
            result = adapter.adapt({"monster_type": monster_type, "name": "Test"})
            assert result["monster_type"] == monster_type

    def test_adapt_normalizes_level(self, adapter: MonsterDataAdapter) -> None:
        """测试等级规范化（范围限制 1-60）。"""
        result = adapter.adapt({"level": -1, "name": "Test"})
        assert result["level"] == 1

        result = adapter.adapt({"level": 100, "name": "Test"})
        assert result["level"] == 60

    def test_adapt_normalizes_negative_stats(self, adapter: MonsterDataAdapter) -> None:
        """测试负数值规范化。"""
        result = adapter.adapt({"hp": -10, "attack": -5, "defense": -3, "speed": -1, "name": "Test"})
        assert result["hp"] == 1
        assert result["attack"] == 0
        assert result["defense"] == 0
        assert result["speed"] == 0

    def test_validate_completeness_full_data(self, adapter: MonsterDataAdapter) -> None:
        """测试完整数据的完整度验证。"""
        raw_data = {
            "monster_key": "test_monster",
            "name": "Test Monster",
            "monster_type": "beast",
            "chapter_id": "chapter_01",
            "region_key": "region_test",
            "level": 1,
            "hp": 10,
            "attack": 5,
            "defense": 0,
            "speed": 5,
            "description": "A test monster.",
            "behavior_pattern": {"aggression": "passive"},
            "loot_table": [{"item_key": "item_test"}],
            "skills": [{"skill_key": "skill_test"}],
        }

        completeness, missing = adapter.validate_completeness(raw_data)

        assert completeness == 1.0
        assert len(missing) == 0

    def test_validate_completeness_missing_fields(self, adapter: MonsterDataAdapter) -> None:
        """测试缺失字段的完整度验证。"""
        raw_data = {"name": "Test"}

        completeness, missing = adapter.validate_completeness(raw_data)

        assert completeness < 1.0
        assert len(missing) > 0
        assert "monster_key" in missing
        assert "hp" in missing

    def test_ensure_minimum_completeness_passes(self, adapter: MonsterDataAdapter) -> None:
        """测试达到最小完整度要求时通过。"""
        raw_data = {
            "monster_key": "test_monster",
            "name": "Test Monster",
            "monster_type": "beast",
            "chapter_id": "chapter_01",
            "region_key": "region_test",
            "level": 1,
            "hp": 10,
            "attack": 5,
            "defense": 0,
            "speed": 5,
            "description": "A test monster.",
            "behavior_pattern": {"aggression": "passive"},
            "loot_table": [{"item_key": "item_test"}],
            "skills": [{"skill_key": "skill_test"}],
        }

        result = adapter.ensure_minimum_completeness(raw_data)

        assert result["monster_key"] == "test_monster"

    def test_ensure_minimum_completeness_fails(self, adapter: MonsterDataAdapter) -> None:
        """测试低于最小完整度要求时抛出异常。"""
        raw_data = {"name": "Test"}

        with pytest.raises(ValueError, match="completeness"):
            adapter.ensure_minimum_completeness(raw_data)

    def test_normalize_behavior_pattern_dict(self, adapter: MonsterDataAdapter) -> None:
        """测试行为模式为字典时保持不变。"""
        bp = {"aggression": "aggressive", "attack_pattern": "ranged"}
        result = adapter.adapt({"behavior_pattern": bp, "name": "Test"})
        assert result["behavior_pattern"] == bp

    def test_normalize_behavior_pattern_non_dict(self, adapter: MonsterDataAdapter) -> None:
        """测试行为模式非字典时使用默认值。"""
        result = adapter.adapt({"behavior_pattern": "aggressive", "name": "Test"})
        assert "aggression" in result["behavior_pattern"]

    def test_normalize_loot_table_list(self, adapter: MonsterDataAdapter) -> None:
        """测试掉落表为列表时保持不变。"""
        loot = [{"item_key": "item_1", "drop_rate": 0.5}]
        result = adapter.adapt({"loot_table": loot, "name": "Test"})
        assert result["loot_table"] == loot

    def test_normalize_skills_list(self, adapter: MonsterDataAdapter) -> None:
        """测试技能为列表时保持不变。"""
        skills = [{"skill_key": "skill_1", "name": "Attack"}]
        result = adapter.adapt({"skills": skills, "name": "Test"})
        assert result["skills"] == skills
