"""区域场景描述数据适配器测试。"""

import pytest

from app.core.region_data_adapter import RegionDataAdapter


@pytest.fixture
def adapter() -> RegionDataAdapter:
    return RegionDataAdapter(chapter_id="chapter_01")


class TestRegionDataAdapter:
    """RegionDataAdapter 测试类。"""

    def test_adapt_complete_data(self, adapter: RegionDataAdapter) -> None:
        """测试完整数据的适配。"""
        raw_data = {
            "region_key": "region_wasteland_01",
            "name": "荒芜之地",
            "chapter_id": "chapter_01",
            "region_type": "expansion",
            "parent_region": "region_core_01",
            "description": "一片被遗忘的荒芜之地，充满了危险和机遇。",
            "lore": "传说这里曾经是一个繁华的王国，后来被一场灾难毁灭。",
            "atmosphere": "荒凉、神秘、危险",
            "visual_style": {
                "terrain_type": "wasteland",
                "color_palette": ["brown", "gray", "red"],
                "lighting": "foggy",
                "architectural_style": "ruined",
            },
            "landmarks": [
                {
                    "landmark_key": "landmark_ruins_01",
                    "name": "古老废墟",
                    "description": "曾经辉煌的城堡废墟。",
                    "type": "ruin",
                    "significance": "重要的探索地点",
                }
            ],
            "danger_level": "high",
            "recommended_level": "20-30",
            "accessibility": "从核心区域向东走即可到达。",
            "climate": "炎热干燥，沙尘暴频繁。",
            "notable_locations": ["废墟入口", "废弃矿坑", "神秘祭坛"],
        }

        result = adapter.adapt(raw_data)

        assert result["region_key"] == "region_wasteland_01"
        assert result["name"] == "荒芜之地"
        assert result["chapter_id"] == "chapter_01"
        assert result["region_type"] == "expansion"
        assert result["parent_region"] == "region_core_01"
        assert result["description"] == "一片被遗忘的荒芜之地，充满了危险和机遇。"
        assert result["lore"] == "传说这里曾经是一个繁华的王国，后来被一场灾难毁灭。"
        assert result["atmosphere"] == "荒凉、神秘、危险"
        assert result["visual_style"]["terrain_type"] == "wasteland"
        assert result["visual_style"]["color_palette"] == ["brown", "gray", "red"]
        assert result["visual_style"]["lighting"] == "foggy"
        assert result["visual_style"]["architectural_style"] == "ruined"
        assert len(result["landmarks"]) == 1
        assert result["landmarks"][0]["landmark_key"] == "landmark_ruins_01"
        assert result["danger_level"] == "high"
        assert result["recommended_level"] == "20-30"
        assert result["accessibility"] == "从核心区域向东走即可到达。"
        assert result["climate"] == "炎热干燥，沙尘暴频繁。"
        assert result["notable_locations"] == ["废墟入口", "废弃矿坑", "神秘祭坛"]

    def test_adapt_missing_fields(self, adapter: RegionDataAdapter) -> None:
        """测试缺失字段时使用默认值。"""
        raw_data = {
            "name": "神秘区域",
        }

        result = adapter.adapt(raw_data)

        assert result["region_key"].startswith("region_")
        assert result["name"] == "神秘区域"
        assert result["chapter_id"] == "chapter_01"
        assert result["region_type"] == "expansion"
        assert result["parent_region"] is None
        assert result["danger_level"] == "medium"
        assert result["recommended_level"] == "1-10"

    def test_adapt_normalizes_region_key(self, adapter: RegionDataAdapter) -> None:
        """测试区域 key 规范化（添加 region_ 前缀）。"""
        result = adapter.adapt({"region_key": "forest_01", "name": "森林"})
        assert result["region_key"] == "region_forest_01"

    def test_adapt_valid_region_types(self, adapter: RegionDataAdapter) -> None:
        """测试所有合法区域类型。"""
        for region_type in ["core", "expansion", "anomaly", "hidden"]:
            result = adapter.adapt({"region_type": region_type, "name": "Test"})
            assert result["region_type"] == region_type

    def test_adapt_invalid_region_type_defaults_to_expansion(self, adapter: RegionDataAdapter) -> None:
        """测试无效区域类型默认为 expansion。"""
        result = adapter.adapt({"region_type": "invalid_type", "name": "Test"})
        assert result["region_type"] == "expansion"

    def test_adapt_valid_danger_levels(self, adapter: RegionDataAdapter) -> None:
        """测试所有合法危险等级。"""
        for danger_level in ["peaceful", "low", "medium", "high", "extreme"]:
            result = adapter.adapt({"danger_level": danger_level, "name": "Test"})
            assert result["danger_level"] == danger_level

    def test_adapt_invalid_danger_level_defaults_to_medium(self, adapter: RegionDataAdapter) -> None:
        """测试无效危险等级默认为 medium。"""
        result = adapter.adapt({"danger_level": "invalid", "name": "Test"})
        assert result["danger_level"] == "medium"

    def test_adapt_valid_terrain_types(self, adapter: RegionDataAdapter) -> None:
        """测试所有合法地形类型。"""
        valid_terrain_types = [
            "plains",
            "forest",
            "mountain",
            "desert",
            "swamp",
            "cave",
            "city",
            "wasteland",
            "volcanic",
            "ocean",
            "lake",
            "river",
            "glacier",
            "jungle",
        ]
        for terrain_type in valid_terrain_types:
            result = adapter.adapt({
                "visual_style": {"terrain_type": terrain_type},
                "name": "Test"
            })
            assert result["visual_style"]["terrain_type"] == terrain_type

    def test_adapt_invalid_terrain_type_defaults_to_plains(self, adapter: RegionDataAdapter) -> None:
        """测试无效地形类型默认为 plains。"""
        result = adapter.adapt({
            "visual_style": {"terrain_type": "invalid"},
            "name": "Test"
        })
        assert result["visual_style"]["terrain_type"] == "plains"

    def test_adapt_normalizes_visual_style(self, adapter: RegionDataAdapter) -> None:
        """测试视觉风格规范化。"""
        result = adapter.adapt({"visual_style": "invalid", "name": "Test"})
        assert result["visual_style"] is not None
        assert result["visual_style"]["terrain_type"] == "plains"

    def test_adapt_normalizes_color_palette(self, adapter: RegionDataAdapter) -> None:
        """测试主色调数组规范化。"""
        result = adapter.adapt({
            "visual_style": {"color_palette": ["red", "green", "blue"]},
            "name": "Test"
        })
        assert result["visual_style"]["color_palette"] == ["red", "green", "blue"]

        result = adapter.adapt({
            "visual_style": {"color_palette": "invalid"},
            "name": "Test"
        })
        assert result["visual_style"]["color_palette"] == ["gray", "brown", "green"]

    def test_adapt_normalizes_landmarks(self, adapter: RegionDataAdapter) -> None:
        """测试地标数组规范化。"""
        raw_data = {
            "landmarks": [
                {
                    "landmark_key": "landmark_01",
                    "name": "地标1",
                    "description": "描述1",
                    "type": "natural",
                    "significance": "重要",
                },
                "invalid",
                {"name": "地标2"},
            ],
            "name": "Test",
        }

        result = adapter.adapt(raw_data)

        assert len(result["landmarks"]) == 2
        assert result["landmarks"][0]["landmark_key"] == "landmark_01"
        assert result["landmarks"][0]["name"] == "地标1"
        assert result["landmarks"][1]["landmark_key"].startswith("landmark_")
        assert result["landmarks"][1]["name"] == "地标2"

    def test_adapt_valid_landmark_types(self, adapter: RegionDataAdapter) -> None:
        """测试所有合法地标类型。"""
        for landmark_type in ["natural", "manmade", "ruin", "mystical"]:
            result = adapter.adapt({
                "landmarks": [{"type": landmark_type}],
                "name": "Test"
            })
            assert result["landmarks"][0]["type"] == landmark_type

    def test_adapt_invalid_landmark_type_defaults_to_natural(self, adapter: RegionDataAdapter) -> None:
        """测试无效地标类型默认为 natural。"""
        result = adapter.adapt({
            "landmarks": [{"type": "invalid"}],
            "name": "Test"
        })
        assert result["landmarks"][0]["type"] == "natural"

    def test_adapt_normalizes_notable_locations(self, adapter: RegionDataAdapter) -> None:
        """测试著名地点数组规范化。"""
        result = adapter.adapt({
            "notable_locations": ["地点1", "地点2"],
            "name": "Test"
        })
        assert result["notable_locations"] == ["地点1", "地点2"]

        result = adapter.adapt({
            "notable_locations": "invalid",
            "name": "Test"
        })
        assert result["notable_locations"] == []

    def test_adapt_normalizes_parent_region(self, adapter: RegionDataAdapter) -> None:
        """测试父区域规范化。"""
        result = adapter.adapt({
            "parent_region": "core_01",
            "name": "Test"
        })
        assert result["parent_region"] == "region_core_01"

        result = adapter.adapt({
            "parent_region": "region_parent_01",
            "name": "Test"
        })
        assert result["parent_region"] == "region_parent_01"

        result = adapter.adapt({
            "parent_region": None,
            "name": "Test"
        })
        assert result["parent_region"] is None

    def test_validate_completeness_full_data(self, adapter: RegionDataAdapter) -> None:
        """测试完整数据的完整度验证。"""
        raw_data = {
            "region_key": "region_test",
            "name": "Test Region",
            "chapter_id": "chapter_01",
            "region_type": "core",
            "description": "Test description",
            "danger_level": "medium",
            "recommended_level": "1-10",
        }

        completeness, missing = adapter.validate_completeness(raw_data)

        assert completeness == 1.0
        assert len(missing) == 0

    def test_validate_completeness_missing_fields(self, adapter: RegionDataAdapter) -> None:
        """测试缺失字段的完整度验证。"""
        raw_data = {"name": "Test"}

        completeness, missing = adapter.validate_completeness(raw_data)

        assert completeness < 1.0
        assert len(missing) > 0
        assert "region_key" in missing
        assert "region_type" in missing
        assert "description" in missing
        assert "danger_level" in missing
        assert "recommended_level" in missing

    def test_ensure_minimum_completeness_passes(self, adapter: RegionDataAdapter) -> None:
        """测试达到最小完整度要求时通过。"""
        raw_data = {
            "region_key": "region_test",
            "name": "Test Region",
            "chapter_id": "chapter_01",
            "region_type": "core",
            "description": "Test description",
            "danger_level": "medium",
            "recommended_level": "1-10",
        }

        result = adapter.ensure_minimum_completeness(raw_data)

        assert result["region_key"] == "region_test"

    def test_ensure_minimum_completeness_fails(self, adapter: RegionDataAdapter) -> None:
        """测试低于最小完整度要求时抛出异常。"""
        raw_data = {"name": "Test"}

        with pytest.raises(ValueError, match="completeness"):
            adapter.ensure_minimum_completeness(raw_data)

    def test_fill_defaults_applies_all(self, adapter: RegionDataAdapter) -> None:
        """测试填充所有默认值。"""
        raw_data = {}

        result = adapter._fill_defaults(raw_data)

        assert result["region_key"].startswith("region_")
        assert result["name"] == "Unknown Region"
        assert result["chapter_id"] == "chapter_01"
        assert result["region_type"] == "expansion"
        assert result["parent_region"] is None
        assert result["description"] == "A mysterious region."
        assert result["lore"] == "Little is known about this place."
        assert result["atmosphere"] == "Unknown atmosphere."
        assert result["visual_style"]["terrain_type"] == "plains"
        assert result["danger_level"] == "medium"
        assert result["recommended_level"] == "1-10"
        assert result["accessibility"] == "Accessible from adjacent regions."
        assert result["climate"] == "Temperate climate."
        assert result["notable_locations"] == []