"""NPC 数据转换适配器测试。"""

import pytest

from app.core.npc_data_adapter import NPCDataAdapter


class TestNPCDataAdapter:
    def test_adapt_converts_raw_npc_data(self):
        adapter = NPCDataAdapter(chapter_id="chapter_01")
        raw_data = {
            "npc_key": "npc_blacksmith_test",
            "name": "Test Smith",
            "title": "Test Blacksmith",
            "gender": "male",
            "age": 45,
            "race": "human",
            "faction_key": "faction_ironward",
            "region_key": "region_core",
            "role": "blacksmith",
            "location_key": "loc_test",
            "description": "A test blacksmith.",
            "personality": ["gruff", "skilled"],
            "traits": ["strong"],
            "voice": "deep",
            "backstory": "Test backstory.",
            "motivation": "Test motivation.",
            "relationship_map": {},
            "dialog_style": "test",
            "dialog_nodes": {
                "first_meet": {"id": "first_meet", "text": "Hello!", "speaker": "npc", "choices": []}
            },
            "quests_given": ["quest_test"],
            "quests_related": [],
            "shop_items": [],
            "services_offered": [],
            "location_x": 100,
            "location_y": 200,
            "interaction_radius": 30,
        }

        adapted = adapter.adapt(raw_data)

        assert adapted["npc_key"] == "npc_blacksmith_test"
        assert adapted["chapter_id"] == "chapter_01"
        assert adapted["name"] == "Test Smith"
        assert adapted["title"] == "Test Blacksmith"
        assert adapted["faction_key"] == "faction_ironward"
        assert adapted["role"] == "blacksmith"
        assert adapted["location_key"] == "loc_test"
        assert adapted["description"] == "A test blacksmith."
        assert adapted["personality"] == ["gruff", "skilled"]
        assert isinstance(adapted["dialogues"], list)
        assert adapted["related_quests"] == ["quest_test"]

    def test_validate_completeness_full_data(self):
        adapter = NPCDataAdapter()
        npc_data = {
            "npc_key": "npc_test",
            "name": "Test NPC",
            "title": "Test",
            "gender": "male",
            "age": 30,
            "race": "human",
            "faction_key": "faction_test",
            "region_key": "region_test",
            "role": "blacksmith",
            "location_key": "loc_test",
            "description": "A test NPC.",
            "personality": ["test"],
            "traits": ["test"],
            "voice": "test",
            "backstory": "Test backstory.",
            "motivation": "Test motivation.",
            "relationship_map": {},
            "dialog_style": "test",
            "dialog_nodes": {},
            "quests_given": [],
            "quests_related": [],
            "shop_items": [],
            "services_offered": [],
            "location_x": 0,
            "location_y": 0,
            "interaction_radius": 30,
        }

        completeness, missing = adapter.validate_completeness(npc_data)

        assert completeness == 1.0
        assert len(missing) == 0

    def test_validate_completeness_missing_fields(self):
        adapter = NPCDataAdapter()
        npc_data = {
            "npc_key": "npc_test",
            "name": "Test NPC",
        }

        completeness, missing = adapter.validate_completeness(npc_data)

        assert completeness < 1.0
        assert len(missing) > 0

    def test_ensure_minimum_completeness_meets_threshold(self):
        adapter = NPCDataAdapter()
        npc_data = {
            "npc_key": "npc_test",
            "name": "Test NPC",
            "title": "Test",
            "gender": "male",
            "age": 30,
            "race": "human",
            "faction_key": "faction_test",
            "region_key": "region_test",
            "role": "blacksmith",
            "location_key": "loc_test",
            "description": "A test NPC.",
            "personality": ["test"],
            "traits": ["test"],
            "voice": "test",
            "backstory": "Test backstory.",
            "motivation": "Test motivation.",
            "relationship_map": {},
            "dialog_style": "test",
            "dialog_nodes": {},
            "quests_given": [],
            "quests_related": [],
            "shop_items": [],
            "services_offered": [],
            "location_x": 0,
            "location_y": 0,
            "interaction_radius": 30,
        }

        result = adapter.ensure_minimum_completeness(npc_data, min_completeness=0.95)

        assert result is not None

    def test_ensure_minimum_completeness_below_threshold(self):
        adapter = NPCDataAdapter()
        npc_data = {
            "npc_key": "npc_test",
            "name": "Test NPC",
        }

        with pytest.raises(ValueError):
            adapter.ensure_minimum_completeness(npc_data, min_completeness=0.95)

    def test_fill_defaults_missing_fields(self):
        adapter = NPCDataAdapter()
        npc_data = {}

        filled = adapter._fill_defaults(npc_data)

        assert filled["npc_key"].startswith("npc_")
        assert filled["name"] == "Unknown NPC"
        assert filled["gender"] == "unknown"
        assert filled["age"] == 30
        assert filled["race"] == "human"
        assert filled["role"] == "commoner"
        assert filled["interaction_radius"] == 30

    def test_normalize_npc_key(self):
        adapter = NPCDataAdapter()

        assert adapter._normalize_npc_key("npc_test") == "npc_test"
        assert adapter._normalize_npc_key("test") == "npc_test"
        assert adapter._normalize_npc_key(None).startswith("npc_")

    def test_normalize_faction_key(self):
        adapter = NPCDataAdapter()

        assert adapter._normalize_faction_key("faction_test") == "faction_test"
        assert adapter._normalize_faction_key("test") == "faction_test"
        assert adapter._normalize_faction_key(None) is None

    def test_convert_dialog_nodes(self):
        adapter = NPCDataAdapter()
        dialog_nodes = {
            "first_meet": {"id": "first_meet", "text": "Hello!", "speaker": "npc"},
            "goodbye": {"id": "goodbye", "text": "", "speaker": "npc"},
        }

        dialogues = adapter._convert_dialog_nodes(dialog_nodes)

        assert isinstance(dialogues, list)
        assert len(dialogues) >= 1
        assert dialogues[0]["id"] == "dia_first_meet"
        assert dialogues[0]["text"] == "Hello!"
        assert dialogues[0]["condition"] == "first_meet"