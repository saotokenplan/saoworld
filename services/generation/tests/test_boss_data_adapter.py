"""Boss 数据适配器测试。"""

import pytest

from app.core.boss_data_adapter import BossDataAdapter


@pytest.fixture
def adapter() -> BossDataAdapter:
    return BossDataAdapter(chapter_id="chapter_02")


class TestBossDataAdapter:
    """BossDataAdapter 测试类。"""

    def test_adapt_complete_boss_data(self, adapter: BossDataAdapter) -> None:
        """测试完整 Boss 数据的适配。"""
        raw_data = {
            "monster_key": "boss_ancient_tree",
            "name": "古树守护者",
            "monster_type": "boss",
            "chapter_id": "chapter_02",
            "region_key": "region_forest_01",
            "level": 12,
            "hp": 800,
            "attack": 28,
            "defense": 15,
            "speed": 3,
            "description": "幽光森林深处的千年古树。",
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
            "is_boss": True,
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
        }

        result = adapter.adapt(raw_data)

        assert result["monster_key"] == "boss_ancient_tree"
        assert result["name"] == "古树守护者"
        assert result["monster_type"] == "boss"
        assert result["is_boss"] is True
        assert result["boss_rank"] == "legendary"
        assert result["phase_count"] == 3
        assert result["enrage_threshold"] == 0.3
        assert len(result["special_skills"]) == 2
        assert "experience" in result["reward"]

    def test_adapt_missing_boss_fields_uses_defaults(self, adapter: BossDataAdapter) -> None:
        """测试缺失 Boss 专属字段时使用默认值。"""
        raw_data = {
            "name": "测试Boss",
            "monster_type": "boss",
        }

        result = adapter.adapt(raw_data)

        assert result["monster_key"].startswith("boss_")
        assert result["is_boss"] is True
        assert result["boss_rank"] == "legendary"
        assert result["phase_count"] == 1
        assert result["enrage_threshold"] == 0.3
        assert result["special_skills"] == []
        assert result["reward"] == {"experience": 1000, "items": []}

    def test_adapt_normalizes_boss_key(self, adapter: BossDataAdapter) -> None:
        """测试 Boss key 规范化（添加 boss_ 前缀）。"""
        result = adapter.adapt({"monster_key": "ancient_tree", "name": "古树守护者"})
        assert result["monster_key"] == "boss_ancient_tree"

    def test_adapt_invalid_boss_rank_defaults_to_legendary(self, adapter: BossDataAdapter) -> None:
        """测试无效的 boss_rank 默认为 legendary。"""
        result = adapter.adapt({"boss_rank": "invalid", "name": "测试Boss"})
        assert result["boss_rank"] == "legendary"

    def test_adapt_valid_boss_ranks(self, adapter: BossDataAdapter) -> None:
        """测试所有合法的 boss_rank。"""
        for rank in ["legendary", "mythic"]:
            result = adapter.adapt({"boss_rank": rank, "name": "测试Boss"})
            assert result["boss_rank"] == rank

    def test_adapt_normalizes_phase_count(self, adapter: BossDataAdapter) -> None:
        """测试阶段数规范化（最小为 1）。"""
        result = adapter.adapt({"phase_count": 0, "name": "测试Boss"})
        assert result["phase_count"] == 1

        result = adapter.adapt({"phase_count": -1, "name": "测试Boss"})
        assert result["phase_count"] == 1

    def test_adapt_normalizes_enrage_threshold(self, adapter: BossDataAdapter) -> None:
        """测试狂暴阈值规范化（范围 0-1）。"""
        result = adapter.adapt({"enrage_threshold": 1.5, "name": "测试Boss"})
        assert result["enrage_threshold"] == 1.0

        result = adapter.adapt({"enrage_threshold": -0.1, "name": "测试Boss"})
        assert result["enrage_threshold"] == 0.0

        result = adapter.adapt({"enrage_threshold": 0.5, "name": "测试Boss"})
        assert result["enrage_threshold"] == 0.5

    def test_adapt_non_dict_reward_uses_default(self, adapter: BossDataAdapter) -> None:
        """测试奖励数据非字典时使用默认值。"""
        result = adapter.adapt({"reward": "test", "name": "测试Boss"})
        assert result["reward"] == {"experience": 1000, "items": []}

    def test_adapt_missing_reward_items_uses_empty_list(self, adapter: BossDataAdapter) -> None:
        """测试奖励中缺失 items 字段时使用空列表。"""
        result = adapter.adapt({"reward": {"experience": 1000}, "name": "测试Boss"})
        assert result["reward"]["experience"] == 1000
        assert result["reward"]["items"] == []

    def test_adapt_non_list_special_skills_uses_empty_list(self, adapter: BossDataAdapter) -> None:
        """测试特殊技能非列表时使用空列表。"""
        result = adapter.adapt({"special_skills": "test", "name": "测试Boss"})
        assert result["special_skills"] == []

    def test_validate_completeness_full_boss_data(self, adapter: BossDataAdapter) -> None:
        """测试完整 Boss 数据的完整度验证。"""
        raw_data = {
            "monster_key": "boss_test",
            "name": "Test Boss",
            "monster_type": "boss",
            "chapter_id": "chapter_02",
            "region_key": "region_test",
            "level": 10,
            "hp": 500,
            "attack": 25,
            "defense": 10,
            "speed": 4,
            "description": "A test boss.",
            "behavior_pattern": {"aggression": "aggressive"},
            "loot_table": [{"item_key": "item_test"}],
            "skills": [{"skill_key": "skill_test"}],
            "is_boss": True,
            "boss_rank": "legendary",
            "phase_count": 2,
            "special_skills": [{"skill_key": "skill_special"}],
            "enrage_threshold": 0.3,
            "reward": {"experience": 3000, "items": []},
        }

        completeness, missing = adapter.validate_completeness(raw_data)

        assert completeness == 1.0
        assert len(missing) == 0

    def test_validate_completeness_missing_boss_fields(self, adapter: BossDataAdapter) -> None:
        """测试缺失 Boss 专属字段的完整度验证。"""
        raw_data = {
            "name": "Test",
            "monster_type": "boss",
        }

        completeness, missing = adapter.validate_completeness(raw_data)

        assert completeness < 1.0
        assert len(missing) > 0
        assert "boss_rank" in missing
        assert "phase_count" in missing
        assert "special_skills" in missing
        assert "enrage_threshold" in missing
        assert "reward" in missing

    def test_ensure_minimum_completeness_passes(self, adapter: BossDataAdapter) -> None:
        """测试达到最小完整度要求时通过。"""
        raw_data = {
            "monster_key": "boss_test",
            "name": "Test Boss",
            "monster_type": "boss",
            "chapter_id": "chapter_02",
            "region_key": "region_test",
            "level": 10,
            "hp": 500,
            "attack": 25,
            "defense": 10,
            "speed": 4,
            "description": "A test boss.",
            "behavior_pattern": {"aggression": "aggressive"},
            "loot_table": [{"item_key": "item_test"}],
            "skills": [{"skill_key": "skill_test"}],
            "is_boss": True,
            "boss_rank": "legendary",
            "phase_count": 2,
            "special_skills": [{"skill_key": "skill_special"}],
            "enrage_threshold": 0.3,
            "reward": {"experience": 3000, "items": []},
        }

        result = adapter.ensure_minimum_completeness(raw_data)

        assert result["monster_key"] == "boss_test"

    def test_ensure_minimum_completeness_fails(self, adapter: BossDataAdapter) -> None:
        """测试低于最小完整度要求时抛出异常。"""
        raw_data = {"name": "Test", "monster_type": "boss"}

        with pytest.raises(ValueError, match="completeness"):
            adapter.ensure_minimum_completeness(raw_data)