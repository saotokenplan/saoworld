"""NPC 生成端到端集成测试。"""

import pytest

from app.core.content_generator import ContentGenerator
from app.core.llm_adapter import MockLLMAdapter


class TestNPCGenerationIntegration:
    @pytest.mark.asyncio
    async def test_generate_npc_uses_adapter_and_scorer(self):
        mock_adapter = MockLLMAdapter()
        mock_adapter.mock_response = {
            "npc_key": "npc_test_blacksmith",
            "name": "Test Smith",
            "title": "Test Blacksmith",
            "gender": "male",
            "age": 45,
            "race": "human",
            "faction_key": "faction_ironward",
            "region_key": "region_core",
            "role": "blacksmith",
            "location_key": "loc_test",
            "description": (
                "A skilled blacksmith who has worked in the forge for over 20 years. "
                "He is known for his exceptional craftsmanship and gruff but honest demeanor."
            ),
            "personality": ["gruff", "skilled", "honest", "proud"],
            "traits": ["strong", "meticulous", "traditional"],
            "voice": "deep and gruff, with a metallic resonance",
            "backstory": (
                "Test Smith was born into a family of skilled craftsmen in the Ironward Alliance. "
                "From a young age, he showed exceptional talent for working with metal, "
                "spending countless hours in the forge alongside his father. Over the years, "
                "he honed his skills and became known throughout the region for creating weapons "
                "and armor of unmatched quality. His dedication to his craft is unmatched, "
                "and he takes great pride in providing adventurers with the tools they need to succeed."
            ),
            "motivation": "To craft the finest weapons and armor for the Ironward Alliance.",
            "relationship_map": {"weapon_merchant": "supplier"},
            "dialog_style": "direct and to the point, often using forging metaphors",
            "dialog_nodes": {
                "first_meet": {"id": "first_meet", "text": "Need a weapon or armor?", "speaker": "npc", "choices": []},
                "about_work": {
                    "id": "about_work", "text": "I've been forging for 20 years.",
                    "speaker": "npc", "choices": [],
                },
                "has_quest": {"id": "has_quest", "text": "I need materials.", "speaker": "npc", "choices": []},
                "quest_accepted": {"id": "quest_accepted", "text": "Great!", "speaker": "npc", "choices": []},
                "quest_completed": {"id": "quest_completed", "text": "Thank you!", "speaker": "npc", "choices": []},
                "default": {"id": "default", "text": "Welcome!", "speaker": "npc", "choices": []},
                "goodbye": {"id": "goodbye", "text": "", "speaker": "npc", "choices": [], "is_end": True},
            },
            "quests_given": ["quest_test"],
            "quests_related": [],
            "shop_items": [],
            "services_offered": ["weapon forging"],
            "location_x": 100,
            "location_y": 200,
            "interaction_radius": 30,
        }

        generator = ContentGenerator(llm_adapter=mock_adapter)
        result = await generator.generate_npc(
            region_id="region_core",
            chapter_id="chapter_01",
            npc_role="blacksmith",
            context={"faction": "Ironward Alliance"},
        )

        assert result is not None
        assert result["npc_key"] == "npc_test_blacksmith"
        assert result["name"] == "Test Smith"
        assert result["role"] == "blacksmith"
        assert "chapter_id" in result

    @pytest.mark.asyncio
    async def test_generate_npc_fails_on_low_completeness(self):
        mock_adapter = MockLLMAdapter()
        mock_adapter.mock_response = {
            "npc_key": "npc_test",
            "name": "Test",
        }

        generator = ContentGenerator(llm_adapter=mock_adapter)

        with pytest.raises(Exception):
            await generator.generate_npc(
                region_id="region_core",
                chapter_id="chapter_01",
                npc_role="blacksmith",
            )

    @pytest.mark.asyncio
    async def test_generate_npc_fails_on_low_quality(self):
        mock_adapter = MockLLMAdapter()
        mock_adapter.mock_response = {
            "npc_key": "npc_test",
            "name": "",
            "title": "",
            "gender": "",
            "age": 0,
            "race": "",
            "faction_key": "",
            "region_key": "",
            "role": "",
            "location_key": "",
            "description": "",
            "personality": [],
            "traits": [],
            "voice": "",
            "backstory": "",
            "motivation": "",
            "relationship_map": {},
            "dialog_style": "",
            "dialog_nodes": {},
            "quests_given": [],
            "quests_related": [],
            "shop_items": [],
            "services_offered": [],
            "location_x": 0,
            "location_y": 0,
            "interaction_radius": 0,
        }

        generator = ContentGenerator(llm_adapter=mock_adapter)

        with pytest.raises(Exception):
            await generator.generate_npc(
                region_id="region_core",
                chapter_id="chapter_01",
                npc_role="blacksmith",
            )

    @pytest.mark.asyncio
    async def test_generate_npc_with_different_roles(self):
        mock_adapter = MockLLMAdapter()
        mock_adapter.mock_response = {
            "npc_key": "npc_test_merchant",
            "name": "Test Merchant",
            "title": "Test Merchant",
            "gender": "female",
            "age": 35,
            "race": "human",
            "faction_key": "faction_harvest",
            "region_key": "region_core",
            "role": "merchant",
            "location_key": "loc_market",
            "description": "A friendly merchant.",
            "personality": ["friendly", "shrewd"],
            "traits": ["charismatic"],
            "voice": "friendly",
            "backstory": "Test backstory.",
            "motivation": "To make profit.",
            "relationship_map": {},
            "dialog_style": "friendly",
            "dialog_nodes": {
                "first_meet": {"id": "first_meet", "text": "Welcome!", "speaker": "npc", "choices": []},
                "goodbye": {"id": "goodbye", "text": "", "speaker": "npc", "choices": [], "is_end": True},
                "about_trade": {"id": "about_trade", "text": "Trade is good.", "speaker": "npc", "choices": []},
                "info": {"id": "info", "text": "I have news.", "speaker": "npc", "choices": []},
                "has_quest": {"id": "has_quest", "text": "I need help.", "speaker": "npc", "choices": []},
                "quest_accepted": {"id": "quest_accepted", "text": "Thanks!", "speaker": "npc", "choices": []},
                "quest_completed": {"id": "quest_completed", "text": "Great!", "speaker": "npc", "choices": []},
                "default": {"id": "default", "text": "Hello!", "speaker": "npc", "choices": []},
            },
            "quests_given": ["quest_test"],
            "quests_related": [],
            "shop_items": [],
            "services_offered": [],
            "location_x": 150,
            "location_y": 250,
            "interaction_radius": 30,
        }

        generator = ContentGenerator(llm_adapter=mock_adapter)

        result = await generator.generate_npc(
            region_id="region_core",
            chapter_id="chapter_01",
            npc_role="merchant",
        )

        assert result["role"] == "merchant"
