import sys
from pathlib import Path

import pytest

_tools_path = Path(__file__).parent.parent.parent
if str(_tools_path) not in sys.path:
    sys.path.insert(0, str(_tools_path))

from content_check.content_safety import ContentSafetyChecker  # noqa: E402
from content_check.base import CheckStatus, IssueSeverity  # noqa: E402


@pytest.fixture
def checker():
    return ContentSafetyChecker({
        "banned_words": ["违禁药品", "赌博"],
        "high_risk_topics": ["自杀", "自残"],
        "target_age_rating": "teen",
    })


class TestContentSafetyChecker:
    def test_pass_with_safe_content(self, checker):
        content = {
            "schema_version": 1,
            "npcs": [
                {
                    "npc_id": "npc_1",
                    "name": "友好的商人",
                    "description": "一个善良的商人，欢迎每一位旅行者。",
                }
            ],
            "quests": [],
        }
        result = checker.check(content)
        assert result.status == CheckStatus.PASSED
        assert result.issues_count == 0

    def test_fail_banned_word(self, checker):
        content = {
            "schema_version": 1,
            "npcs": [
                {
                    "npc_id": "npc_1",
                    "name": "可疑人物",
                    "description": "他在偷偷贩卖违禁药品。",
                }
            ],
            "quests": [],
        }
        result = checker.check(content)
        assert any(i.issue_type == "banned_word_found" for i in result.issues)
        assert any(i.severity == IssueSeverity.CRITICAL for i in result.issues)

    def test_high_risk_topic(self, checker):
        content = {
            "schema_version": 1,
            "quests": [
                {
                    "quest_id": "quest_1",
                    "title": "黑暗的任务",
                    "description": "一个关于自杀的故事。",
                }
            ],
        }
        result = checker.check(content)
        assert any(i.issue_type == "high_risk_topic" for i in result.issues)
        assert any(i.severity == IssueSeverity.HIGH for i in result.issues)

    def test_mature_theme(self, checker):
        content = {
            "schema_version": 1,
            "quests": [
                {
                    "quest_id": "quest_1",
                    "title": "血腥任务",
                    "description": "充满血腥的战斗场景。",
                }
            ],
        }
        result = checker.check(content)
        assert any(i.issue_type == "mature_theme" for i in result.issues)

    def test_extreme_violence(self, checker):
        content = {
            "schema_version": 1,
            "quests": [
                {
                    "quest_id": "quest_1",
                    "title": "恐怖任务",
                    "description": "敌人被虐杀的场景令人发指。",
                }
            ],
        }
        result = checker.check(content)
        assert any(i.issue_type == "extreme_violence" for i in result.issues)
        assert any(i.severity == IssueSeverity.CRITICAL for i in result.issues)

    def test_nested_content_checked(self, checker):
        content = {
            "schema_version": 1,
            "npcs": [
                {
                    "npc_id": "npc_1",
                    "dialogues": [
                        {"id": "d1", "text": "让我们来赌博吧！"},
                    ],
                }
            ],
            "quests": [],
        }
        result = checker.check(content)
        assert any(i.issue_type == "banned_word_found" for i in result.issues)

    def test_score_calculation(self, checker):
        content = {
            "schema_version": 1,
            "quests": [
                {
                    "quest_id": "quest_1",
                    "description": "包含自杀主题的描述。",
                }
            ],
        }
        result = checker.check(content)
        assert result.score < 100
        assert result.score > 0

    def test_all_age_rating_escalates_mature_theme(self):
        checker = ContentSafetyChecker({
            "banned_words": [],
            "high_risk_topics": [],
            "target_age_rating": "all",
        })
        content = {
            "schema_version": 1,
            "quests": [
                {
                    "quest_id": "quest_1",
                    "description": "这是一段包含血腥和死亡描写的内容。",
                }
            ],
        }

        result = checker.check(content)

        mature_issues = [issue for issue in result.issues if issue.issue_type == "mature_theme"]
        assert mature_issues
        assert all(issue.severity == IssueSeverity.HIGH for issue in mature_issues)

    def test_banned_word_threshold_exceeded_adds_aggregate_issue(self):
        checker = ContentSafetyChecker({
            "banned_words": ["违禁药品", "赌博"],
            "high_risk_topics": [],
            "target_age_rating": "teen",
            "max_banned_words_per_content": 1,
        })
        content = {
            "schema_version": 1,
            "npcs": [
                {
                    "npc_id": "npc_1",
                    "description": "他售卖违禁药品，还组织赌博。",
                }
            ],
        }

        result = checker.check(content)

        assert any(issue.issue_type == "banned_word_threshold_exceeded" for issue in result.issues)
