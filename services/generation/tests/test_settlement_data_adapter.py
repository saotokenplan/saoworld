"""聚落数据转换适配器测试。"""

import pytest

from app.core.settlement_data_adapter import SettlementDataAdapter


class TestSettlementDataAdapter:
    def test_adapt_converts_raw_settlement_data(self):
        adapter = SettlementDataAdapter()
        raw_data = {
            "settlement_key": "settlement_village_test",
            "name": "晨光村",
            "settlement_type": "village",
            "region_key": "region_core",
            "chapter_id": "chapter_01",
            "faction_key": "faction_iron_guard",
            "description": "一座宁静的小村庄，以农业为主。",
            "population": 200,
            "main_resources": ["谷物", "木材"],
            "economy_type": "agriculture",
            "status": "peaceful",
            "notable_locations": [
                {"location_key": "loc_center", "name": "广场", "description": "村庄中心广场"},
            ],
            "key_npcs": ["npc_leader_01"],
            "faction_influence": {"faction_iron_guard": "主导"},
            "relationships": {},
            "history": "村庄建于数百年前。",
            "culture": "民风淳朴。",
            "defenses": ["木墙"],
            "services": ["旅馆", "商店"],
            "special_features": ["市集"],
            "location_x": 100,
            "location_y": 200,
        }

        adapted = adapter.adapt(raw_data)

        assert adapted["settlement_key"] == "settlement_village_test"
        assert adapted["name"] == "晨光村"
        assert adapted["settlement_type"] == "village"
        assert adapted["region_key"] == "region_core"
        assert adapted["chapter_id"] == "chapter_01"
        assert adapted["description"] == "一座宁静的小村庄，以农业为主。"
        assert adapted["population"] == 200
        assert adapted["main_resources"] == ["谷物", "木材"]
        assert adapted["economy_type"] == "agriculture"
        assert adapted["status"] == "peaceful"

    def test_validate_completeness_full_data(self):
        adapter = SettlementDataAdapter()
        settlement_data = {
            "settlement_key": "settlement_test",
            "name": "测试村",
            "settlement_type": "village",
            "region_key": "region_core",
            "chapter_id": "chapter_01",
            "description": "测试描述。",
            "population": 100,
            "main_resources": ["资源1"],
            "economy_type": "agriculture",
            "status": "peaceful",
            "notable_locations": [],
            "key_npcs": [],
            "faction_influence": {},
            "relationships": {},
            "history": "测试历史。",
            "culture": "测试文化。",
            "defenses": [],
            "services": [],
            "special_features": [],
            "location_x": 0,
            "location_y": 0,
        }

        completeness, missing = adapter.validate_completeness(settlement_data)

        assert completeness == 1.0
        assert len(missing) == 0

    def test_validate_completeness_missing_fields(self):
        adapter = SettlementDataAdapter()
        settlement_data = {
            "settlement_key": "settlement_test",
            "name": "测试村",
        }

        completeness, missing = adapter.validate_completeness(settlement_data)

        assert completeness < 1.0
        assert len(missing) > 0

    def test_ensure_minimum_completeness_meets_threshold(self):
        adapter = SettlementDataAdapter()
        settlement_data = {
            "settlement_key": "settlement_test",
            "name": "测试村",
            "settlement_type": "village",
            "region_key": "region_core",
            "chapter_id": "chapter_01",
            "description": "测试描述。",
            "population": 100,
            "main_resources": ["资源1"],
            "economy_type": "agriculture",
            "status": "peaceful",
            "notable_locations": [],
            "key_npcs": [],
            "faction_influence": {},
            "relationships": {},
            "history": "测试历史。",
            "culture": "测试文化。",
            "defenses": [],
            "services": [],
            "special_features": [],
            "location_x": 0,
            "location_y": 0,
        }

        result = adapter.ensure_minimum_completeness(settlement_data, min_completeness=0.90)

        assert result is not None

    def test_ensure_minimum_completeness_below_threshold(self):
        adapter = SettlementDataAdapter()
        settlement_data = {
            "settlement_key": "settlement_test",
            "name": "测试村",
        }

        with pytest.raises(ValueError):
            adapter.ensure_minimum_completeness(settlement_data, min_completeness=0.90)

    def test_fill_defaults_missing_fields(self):
        adapter = SettlementDataAdapter()
        settlement_data = {}

        filled = adapter._fill_defaults(settlement_data)

        assert filled["settlement_key"].startswith("settlement_")
        assert filled["name"] == "Unknown Settlement"
        assert filled["settlement_type"] == "village"
        assert filled["region_key"] == "region_unknown"
        assert filled["chapter_id"] == "chapter_01"
        assert filled["population"] == 50
        assert filled["economy_type"] == "agriculture"
        assert filled["status"] == "peaceful"

    def test_normalize_settlement_key(self):
        adapter = SettlementDataAdapter()

        assert adapter._normalize_settlement_key("settlement_test") == "settlement_test"
        assert adapter._normalize_settlement_key("test") == "settlement_test"
        assert adapter._normalize_settlement_key(None).startswith("settlement_")

    def test_normalize_faction_key(self):
        adapter = SettlementDataAdapter()

        assert adapter._normalize_faction_key("faction_test") == "faction_test"
        assert adapter._normalize_faction_key("test") == "faction_test"
        assert adapter._normalize_faction_key(None) is None

    def test_normalize_region_key(self):
        adapter = SettlementDataAdapter()

        assert adapter._normalize_region_key("region_test") == "region_test"
        assert adapter._normalize_region_key("test") == "region_test"
        assert adapter._normalize_region_key(None) is None
