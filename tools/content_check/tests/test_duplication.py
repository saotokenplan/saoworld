import sys
from pathlib import Path

import pytest

_tools_path = Path(__file__).parent.parent.parent
if str(_tools_path) not in sys.path:
    sys.path.insert(0, str(_tools_path))

from content_check.duplication import DuplicationChecker  # noqa: E402
from content_check.base import CheckStatus  # noqa: E402


@pytest.fixture
def checker():
    return DuplicationChecker({
        "npc_similarity_threshold": 0.9,
        "quest_skeleton_reuse_threshold": 0.9,
        "text_paragraph_repeat_threshold": 0.9,
        "min_text_length_for_check": 10,
    })


class TestDuplicationChecker:
    def test_pass_unique_content(self, checker):
        content = {
            "schema_version": 1,
            "npcs": [
                {
                    "npc_id": "npc_1",
                    "name": "铁匠",
                    "faction": "faction_ironward",
                    "role": "craftsman",
                    "personality": ["gruff", "skilled"],
                    "description": "一位技艺精湛的铁匠。",
                },
                {
                    "npc_id": "npc_2",
                    "name": "商人",
                    "faction": "faction_harvest",
                    "role": "merchant",
                    "personality": ["friendly", "shrewd"],
                    "description": "一位精明的商人。",
                },
            ],
            "quests": [],
        }
        result = checker.check(content)
        assert result.status == CheckStatus.PASSED

    def test_duplicate_npc_id(self, checker):
        content = {
            "schema_version": 1,
            "npcs": [
                {"npc_id": "npc_dup", "name": "NPC A"},
                {"npc_id": "npc_dup", "name": "NPC B"},
            ],
            "quests": [],
        }
        result = checker.check(content)
        assert any(i.issue_type == "duplicate_npc_id" for i in result.issues)

    def test_duplicate_quest_id(self, checker):
        content = {
            "schema_version": 1,
            "npcs": [],
            "quests": [
                {"quest_id": "quest_dup", "title": "Quest A"},
                {"quest_id": "quest_dup", "title": "Quest B"},
            ],
        }
        result = checker.check(content)
        assert any(i.issue_type == "duplicate_quest_id" for i in result.issues)

    def test_high_npc_similarity(self, checker):
        checker_high = DuplicationChecker({
            "npc_similarity_threshold": 0.3,
            "quest_skeleton_reuse_threshold": 0.9,
            "text_paragraph_repeat_threshold": 0.9,
            "min_text_length_for_check": 10,
        })
        content = {
            "schema_version": 1,
            "npcs": [
                {
                    "npc_id": "npc_1",
                    "name": "NPC 1",
                    "faction": "faction_same",
                    "role": "warrior",
                    "personality": ["brave", "strong"],
                    "description": "一位勇敢强壮的战士，守卫着村庄。",
                },
                {
                    "npc_id": "npc_2",
                    "name": "NPC 2",
                    "faction": "faction_same",
                    "role": "warrior",
                    "personality": ["brave", "strong"],
                    "description": "一位勇敢强壮的战士，守卫着村庄。",
                },
            ],
            "quests": [],
        }
        result = checker_high.check(content)
        assert any(i.issue_type == "npc_similarity_too_high" for i in result.issues)

    def test_no_duplication_in_single_item(self, checker):
        content = {
            "schema_version": 1,
            "npcs": [
                {"npc_id": "npc_1", "name": "Only NPC"},
            ],
            "quests": [
                {"quest_id": "quest_1", "title": "Only Quest"},
            ],
        }
        result = checker.check(content)
        assert result.issues_count == 0

    def test_with_existing_content(self, checker):
        checker_high = DuplicationChecker({
            "npc_similarity_threshold": 0.5,
            "quest_skeleton_reuse_threshold": 0.9,
            "text_paragraph_repeat_threshold": 0.9,
            "min_text_length_for_check": 10,
        })
        new_content = {
            "schema_version": 1,
            "npcs": [
                {
                    "npc_id": "npc_new",
                    "name": "新铁匠",
                    "faction": "faction_ironward",
                    "role": "craftsman",
                    "personality": ["skilled", "honest"],
                    "description": "一位技艺精湛的铁匠。",
                }
            ],
            "quests": [],
        }
        existing_content = {
            "npcs": [
                {
                    "npc_id": "npc_old",
                    "name": "老铁匠",
                    "faction": "faction_ironward",
                    "role": "craftsman",
                    "personality": ["skilled", "honest"],
                    "description": "一位技艺精湛的老铁匠。",
                }
            ],
        }
        result = checker_high.check(new_content, {"existing_content": existing_content})
        assert any(i.issue_type == "npc_similarity_too_high" for i in result.issues)
