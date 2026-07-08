import sys
from pathlib import Path

import pytest

_tools_path = Path(__file__).parent.parent.parent
if str(_tools_path) not in sys.path:
    sys.path.insert(0, str(_tools_path))

from content_check.reward_boundary import RewardBoundaryChecker  # noqa: E402
from content_check.base import CheckStatus  # noqa: E402


@pytest.fixture
def checker():
    return RewardBoundaryChecker({
        "chapter_exp_limits": {
            "chapter_01": 500,
            "chapter_02": 1500,
        },
        "chapter_gold_limits": {
            "chapter_01": 100,
            "chapter_02": 300,
        },
        "region_level_ranges": {
            "region_test": [1, 10],
        },
    })


class TestRewardBoundaryChecker:
    def test_pass_with_valid_content(self, checker):
        content = {
            "schema_version": 1,
            "quests": [
                {
                    "quest_id": "quest_1",
                    "chapter": "chapter_01",
                    "rewards": {"experience": 100, "gold": 20},
                }
            ],
        }
        result = checker.check(content)
        assert result.status == CheckStatus.PASSED
        assert result.score >= 75

    def test_chapter_exceeded(self, checker):
        content = {
            "schema_version": 1,
            "quests": [
                {
                    "quest_id": "quest_1",
                    "chapter": "chapter_01",
                    "rewards": {"experience": 600},
                }
            ],
        }
        result = checker.check(content)
        assert any(i.issue_type == "chapter_exp_exceeded" for i in result.issues)

    def test_gold_exceeded(self, checker):
        content = {
            "schema_version": 1,
            "quests": [
                {
                    "quest_id": "quest_1",
                    "chapter": "chapter_01",
                    "rewards": {"gold": 200},
                }
            ],
        }
        result = checker.check(content)
        assert any(i.issue_type == "chapter_gold_exceeded" for i in result.issues)

    def test_multiple_quests_accumulate(self, checker):
        content = {
            "schema_version": 1,
            "quests": [
                {
                    "quest_id": "quest_1",
                    "chapter": "chapter_01",
                    "rewards": {"experience": 300},
                },
                {
                    "quest_id": "quest_2",
                    "chapter": "chapter_01",
                    "rewards": {"experience": 300},
                },
            ],
        }
        result = checker.check(content)
        assert any(i.issue_type == "chapter_exp_exceeded" for i in result.issues)

    def test_no_chapter_no_check(self, checker):
        content = {
            "schema_version": 1,
            "quests": [
                {
                    "quest_id": "quest_1",
                    "rewards": {"experience": 99999},
                }
            ],
        }
        result = checker.check(content)
        assert not any(i.issue_type == "chapter_exp_exceeded" for i in result.issues)

    def test_quest_level_above_region(self, checker):
        content = {
            "schema_version": 1,
            "quests": [
                {
                    "quest_id": "quest_1",
                    "region": "region_test",
                    "rewards": {"experience": 5000},
                    "objectives": [
                        {"id": "1", "type": "combat"},
                        {"id": "2", "type": "explore"},
                        {"id": "3", "type": "collect"},
                    ],
                }
            ],
        }
        result = checker.check(content)
        assert any(i.issue_type == "quest_level_above_region" for i in result.issues)

    def test_no_region_no_level_check(self, checker):
        content = {
            "schema_version": 1,
            "quests": [
                {
                    "quest_id": "quest_1",
                    "rewards": {"experience": 99999},
                    "objectives": [{"id": "1"}],
                }
            ],
        }
        result = checker.check(content)
        assert not any(i.issue_type == "quest_level_above_region" for i in result.issues)
