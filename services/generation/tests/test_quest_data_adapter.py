"""任务数据转换适配器测试。"""

import pytest

from app.core.quest_data_adapter import QuestDataAdapter


class TestQuestDataAdapter:
    def test_adapt_converts_raw_quest_data(self):
        adapter = QuestDataAdapter(chapter_id="chapter_01")
        raw_data = {
            "quest_key": "quest_side_test",
            "title": "测试支线任务",
            "description": "一个测试支线任务描述",
            "quest_type": "side",
            "chapter_id": "chapter_01",
            "region_key": "region_core",
            "start_npc_key": "npc_test_start",
            "end_npc_key": "npc_test_end",
            "prerequisites": ["quest_main_ch01"],
            "objectives": [
                {"id": "obj_1", "description": "目标1", "type": "npc", "target": "npc_test", "completed": False},
                {"id": "obj_2", "description": "目标2", "type": "combat", "target": 5, "completed": False},
            ],
            "rewards": {"experience": 150, "gold": 50, "reputation": {"faction_ironward": 30}, "items": []},
            "failure_condition": {"type": "time_limit", "minutes": 30},
        }

        adapted = adapter.adapt(raw_data)

        assert adapted["quest_key"] == "quest_side_test"
        assert adapted["chapter_id"] == "chapter_01"
        assert adapted["title"] == "测试支线任务"
        assert adapted["description"] == "一个测试支线任务描述"
        assert adapted["quest_type"] == "side"
        assert adapted["region_key"] == "region_core"
        assert adapted["start_npc_key"] == "npc_test_start"
        assert adapted["end_npc_key"] == "npc_test_end"
        assert adapted["prerequisites"] == ["quest_main_ch01"]
        assert len(adapted["objectives"]) == 2
        assert adapted["objectives"][0]["id"] == "obj_1"
        assert adapted["objectives"][0]["type"] == "npc"
        assert adapted["rewards"]["experience"] == 150
        assert adapted["rewards"]["gold"] == 50
        assert adapted["failure_condition"] == {"type": "time_limit", "minutes": 30}

    def test_validate_completeness_full_data(self):
        adapter = QuestDataAdapter()
        quest_data = {
            "quest_key": "quest_test",
            "title": "测试任务",
            "description": "测试任务描述",
            "quest_type": "side",
            "chapter_id": "chapter_01",
            "region_key": "region_core",
            "objectives": [{"id": "obj_1", "description": "目标1", "type": "npc", "target": "npc_test", "completed": False}],
        }

        completeness, missing = adapter.validate_completeness(quest_data)

        assert completeness == 1.0
        assert len(missing) == 0

    def test_validate_completeness_missing_fields(self):
        adapter = QuestDataAdapter()
        quest_data = {
            "quest_key": "quest_test",
            "title": "测试任务",
        }

        completeness, missing = adapter.validate_completeness(quest_data)

        assert completeness < 1.0
        assert len(missing) > 0

    def test_ensure_minimum_completeness_meets_threshold(self):
        adapter = QuestDataAdapter()
        quest_data = {
            "quest_key": "quest_test",
            "title": "测试任务",
            "description": "测试任务描述",
            "quest_type": "side",
            "chapter_id": "chapter_01",
            "region_key": "region_core",
            "objectives": [{"id": "obj_1", "description": "目标1", "type": "npc", "target": "npc_test", "completed": False}],
        }

        result = adapter.ensure_minimum_completeness(quest_data, min_completeness=0.95)

        assert result is not None

    def test_ensure_minimum_completeness_below_threshold(self):
        adapter = QuestDataAdapter()
        quest_data = {
            "quest_key": "quest_test",
            "title": "测试任务",
        }

        with pytest.raises(ValueError):
            adapter.ensure_minimum_completeness(quest_data, min_completeness=0.95)

    def test_fill_defaults_missing_fields(self):
        adapter = QuestDataAdapter()
        quest_data = {}

        filled = adapter._fill_defaults(quest_data)

        assert filled["quest_key"].startswith("quest_")
        assert filled["title"] == "Unknown Quest"
        assert filled["description"] == "A mysterious quest."
        assert filled["quest_type"] == "side"
        assert filled["chapter_id"] == "chapter_01"
        assert filled["region_key"] == "region_unknown"
        assert len(filled["objectives"]) == 1
        assert filled["rewards"] == {"experience": 100, "gold": 50, "reputation": {}, "items": []}

    def test_normalize_quest_key(self):
        adapter = QuestDataAdapter()

        assert adapter._normalize_quest_key("quest_test") == "quest_test"
        assert adapter._normalize_quest_key("test") == "quest_test"
        assert adapter._normalize_quest_key(None).startswith("quest_")

    def test_normalize_quest_type(self):
        adapter = QuestDataAdapter()

        assert adapter._normalize_quest_type("main") == "main"
        assert adapter._normalize_quest_type("side") == "side"
        assert adapter._normalize_quest_type("event") == "event"
        assert adapter._normalize_quest_type("daily") == "daily"
        assert adapter._normalize_quest_type("unknown") == "side"
        assert adapter._normalize_quest_type(None) == "side"

    def test_normalize_region_key(self):
        adapter = QuestDataAdapter()

        assert adapter._normalize_region_key("region_test") == "region_test"
        assert adapter._normalize_region_key("test") == "region_test"
        assert adapter._normalize_region_key(None) is None

    def test_normalize_objectives(self):
        adapter = QuestDataAdapter()
        objectives = [
            {"id": "obj_1", "description": "目标1", "type": "npc", "target": "npc_test", "completed": False},
            {"id": "obj_2", "description": "目标2", "type": "invalid_type", "target": 5, "completed": True},
        ]

        normalized = adapter._normalize_objectives(objectives)

        assert len(normalized) == 2
        assert normalized[0]["id"] == "obj_1"
        assert normalized[0]["type"] == "npc"
        assert not normalized[0]["completed"]
        assert normalized[1]["type"] == "story"

    def test_normalize_rewards(self):
        adapter = QuestDataAdapter()
        rewards = {"experience": 100, "gold": 50, "reputation": {"faction_test": 20}, "items": ["item1"]}

        normalized = adapter._normalize_rewards(rewards)

        assert normalized["experience"] == 100
        assert normalized["gold"] == 50
        assert normalized["reputation"] == {"faction_test": 20}
        assert normalized["items"] == ["item1"]

    def test_normalize_failure_condition(self):
        adapter = QuestDataAdapter()

        fc = adapter._normalize_failure_condition({"type": "time_limit", "minutes": 30})
        assert fc == {"type": "time_limit", "minutes": 30}

        fc = adapter._normalize_failure_condition({"type": "time_limit", "minutes": 0})
        assert fc is None

        fc = adapter._normalize_failure_condition(None)
        assert fc is None