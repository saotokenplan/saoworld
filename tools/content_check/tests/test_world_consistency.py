import sys
from pathlib import Path

import pytest

_tools_path = Path(__file__).parent.parent.parent
if str(_tools_path) not in sys.path:
    sys.path.insert(0, str(_tools_path))

from content_check.world_consistency import WorldConsistencyChecker  # noqa: E402
from content_check.base import CheckStatus, IssueSeverity  # noqa: E402


@pytest.fixture
def checker():
    return WorldConsistencyChecker()


class TestWorldConsistencyChecker:
    def test_pass_with_valid_content(self, checker):
        content = {
            "schema_version": 1,
            "npcs": [],
            "quests": [],
        }
        result = checker.check(content)
        assert result.status == CheckStatus.PASSED
        assert result.score == 100.0
        assert result.issues_count == 0

    def test_fail_missing_schema_version(self, checker):
        content = {
            "npcs": [],
            "quests": [],
        }
        result = checker.check(content)
        assert result.issues_count > 0
        assert any(i.issue_type == "missing_schema_version" for i in result.issues)

    def test_fail_invalid_schema_version(self, checker):
        content = {
            "schema_version": 0,
            "npcs": [],
            "quests": [],
        }
        result = checker.check(content)
        assert any(i.issue_type == "invalid_schema_version" for i in result.issues)

    def test_unknown_faction_in_npc(self, checker):
        content = {
            "schema_version": 1,
            "npcs": [
                {
                    "npc_id": "npc_test",
                    "name": "Test NPC",
                    "faction": "faction_unknown",
                }
            ],
            "quests": [],
        }
        context = {
            "factions": {"faction_ironward": {"name": "铁卫联盟"}},
        }
        result = checker.check(content, context)
        assert any(i.issue_type == "unknown_faction" for i in result.issues)

    def test_quest_outside_chapter(self, checker):
        content = {
            "schema_version": 1,
            "npcs": [],
            "quests": [
                {
                    "quest_id": "quest_test",
                    "title": "Test Quest",
                    "chapter": "chapter_99",
                    "prerequisites": [],
                }
            ],
        }
        context = {
            "chapters": [{"chapter_id": "chapter_01"}, {"chapter_id": "chapter_02"}],
        }
        result = checker.check(content, context)
        assert any(i.issue_type == "quest_outside_chapter" for i in result.issues)

    def test_exp_reward_mismatch(self, checker):
        content = {
            "schema_version": 1,
            "npcs": [],
            "quests": [
                {
                    "quest_id": "quest_test",
                    "title": "Test Quest",
                    "region": "region_test",
                    "rewards": {"experience": 99999},
                    "objectives": [{"id": "obj_1", "description": "test"}],
                }
            ],
        }
        context = {
            "regions": {
                "region_test": {
                    "level_range": [1, 10],
                    "risk_level": "low",
                }
            },
        }
        result = checker.check(content, context)
        assert any(i.issue_type == "exp_reward_mismatch" for i in result.issues)

    def test_mainline_npc_protected(self, checker):
        content = {
            "schema_version": 1,
            "npcs": [
                {
                    "npc_id": "npc_protected",
                    "name": "Protected NPC",
                    "description": "Modified description",
                }
            ],
            "quests": [],
        }
        context = {
            "protected_mainline_elements": {"npc_protected"},
        }
        result = checker.check(content, context)
        assert any(i.issue_type == "mainline_npc_modified" for i in result.issues)
        assert any(i.severity == IssueSeverity.CRITICAL for i in result.issues)

    def test_result_to_dict(self, checker):
        content = {"schema_version": 1, "npcs": [], "quests": []}
        result = checker.check(content)
        result_dict = result.to_dict()
        assert "check_name" in result_dict
        assert "status" in result_dict
        assert "score" in result_dict
        assert "issues_count" in result_dict
        assert "issues" in result_dict
