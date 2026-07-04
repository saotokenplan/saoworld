from typing import Any

from .base import BaseChecker, CheckResult, CheckStatus, IssueSeverity


class RewardBoundaryChecker(BaseChecker):
    name = "reward_boundary"

    def check(self, content_data: dict[str, Any], context: dict[str, Any] | None = None) -> CheckResult:
        context = context or {}
        result = CheckResult(
            check_name=self.name,
            status=CheckStatus.PASSED,
            score=100.0,
        )

        self._check_chapter_exp_limits(content_data, result)
        self._check_chapter_gold_limits(content_data, result)
        self._check_region_level_range(content_data, context, result)
        self._check_repeatable_reward_cap(content_data, context, result)
        self._check_resource_refresh_rate(content_data, context, result)

        result.score = self._calculate_score(result.issues)
        result.status = self._determine_status(result.score, result.issues)

        return result

    def _check_chapter_exp_limits(self, content_data: dict[str, Any], result: CheckResult) -> None:
        chapter_exp_limits = self.config.get("chapter_exp_limits", {})
        if not chapter_exp_limits:
            return

        chapter_exp_totals: dict[str, int] = {}

        quests = content_data.get("quests", [])
        for quest in quests:
            chapter = quest.get("chapter")
            if not chapter:
                continue

            rewards = quest.get("rewards", {})
            exp = rewards.get("experience", 0)
            chapter_exp_totals[chapter] = chapter_exp_totals.get(chapter, 0) + exp

        for chapter, total_exp in chapter_exp_totals.items():
            limit = chapter_exp_limits.get(chapter)
            if limit and total_exp > limit:
                result.add_issue(
                    issue_type="chapter_exp_exceeded",
                    severity=IssueSeverity.HIGH,
                    message=f"章节 {chapter} 的任务总经验 {total_exp} 超过上限 {limit}",
                    location=f"chapters.{chapter}.experience_total",
                    details={"chapter": chapter, "total_exp": total_exp, "limit": limit},
                )

    def _check_chapter_gold_limits(self, content_data: dict[str, Any], result: CheckResult) -> None:
        chapter_gold_limits = self.config.get("chapter_gold_limits", {})
        if not chapter_gold_limits:
            return

        chapter_gold_totals: dict[str, int] = {}

        quests = content_data.get("quests", [])
        for quest in quests:
            chapter = quest.get("chapter")
            if not chapter:
                continue

            rewards = quest.get("rewards", {})
            gold = rewards.get("gold", 0)
            chapter_gold_totals[chapter] = chapter_gold_totals.get(chapter, 0) + gold

        for chapter, total_gold in chapter_gold_totals.items():
            limit = chapter_gold_limits.get(chapter)
            if limit and total_gold > limit:
                result.add_issue(
                    issue_type="chapter_gold_exceeded",
                    severity=IssueSeverity.HIGH,
                    message=f"章节 {chapter} 的任务总金币 {total_gold} 超过上限 {limit}",
                    location=f"chapters.{chapter}.gold_total",
                    details={"chapter": chapter, "total_gold": total_gold, "limit": limit},
                )

    def _check_region_level_range(
        self, content_data: dict[str, Any], context: dict[str, Any], result: CheckResult
    ) -> None:
        region_level_ranges = self.config.get("region_level_ranges", {})
        if not region_level_ranges:
            return

        quests = content_data.get("quests", [])
        for quest in quests:
            region_id = quest.get("region")
            if not region_id:
                continue

            level_range = region_level_ranges.get(region_id)
            if not level_range:
                continue

            min_level, max_level = level_range
            rewards = quest.get("rewards", {})
            exp = rewards.get("experience", 0)

            objectives = quest.get("objectives", [])
            estimated_level = _estimate_quest_level(len(objectives), exp)

            if estimated_level > max_level:
                result.add_issue(
                    issue_type="quest_level_above_region",
                    severity=IssueSeverity.MEDIUM,
                    message=f"任务 {quest.get('title', quest.get('quest_id'))} 的预估等级 {estimated_level} 超出区域 {region_id} 的上限 {max_level}",
                    location=f"quests.{quest.get('quest_id', 'unknown')}",
                    details={
                        "quest_id": quest.get("quest_id"),
                        "estimated_level": estimated_level,
                        "region_id": region_id,
                        "region_level_range": level_range,
                    },
                )

    def _check_repeatable_reward_cap(
        self, content_data: dict[str, Any], context: dict[str, Any], result: CheckResult
    ) -> None:
        multiplier_cap = self.config.get("repeatable_reward_multiplier_cap", 0.5)
        if multiplier_cap <= 0:
            return

        quests = content_data.get("quests", [])
        quest_map = {q.get("quest_id"): q for q in quests}

        for quest in quests:
            quest_type = quest.get("type", "side")
            if quest_type != "repeatable":
                continue

            base_quest_id = quest.get("base_quest_id")
            if not base_quest_id or base_quest_id not in quest_map:
                continue

            base_quest = quest_map[base_quest_id]
            base_exp = base_quest.get("rewards", {}).get("experience", 0)
            repeat_exp = quest.get("rewards", {}).get("experience", 0)

            if base_exp > 0 and repeat_exp > base_exp * multiplier_cap:
                result.add_issue(
                    issue_type="repeatable_reward_too_high",
                    severity=IssueSeverity.HIGH,
                    message=f"可重复任务 {quest.get('title', quest.get('quest_id'))} 的经验奖励 {repeat_exp} 超过基础任务的 {multiplier_cap * 100}% 上限",
                    location=f"quests.{quest.get('quest_id', 'unknown')}.rewards.experience",
                    details={
                        "quest_id": quest.get("quest_id"),
                        "base_quest_id": base_quest_id,
                        "base_exp": base_exp,
                        "repeat_exp": repeat_exp,
                        "cap_multiplier": multiplier_cap,
                    },
                )

    def _check_resource_refresh_rate(
        self, content_data: dict[str, Any], context: dict[str, Any], result: CheckResult
    ) -> None:
        regions = context.get("regions", {})
        if not regions:
            return

        resource_nodes = content_data.get("resource_nodes", [])
        for node in resource_nodes:
            region_id = node.get("region_id")
            if not region_id or region_id not in regions:
                continue

            region = regions[region_id]
            resource_level = region.get("resource_level", "medium")
            refresh_rate = node.get("refresh_rate_minutes")

            if not refresh_rate:
                continue

            min_refresh_by_level = {
                "low": 120,
                "medium": 60,
                "high": 30,
            }
            min_refresh = min_refresh_by_level.get(resource_level, 60)

            if refresh_rate < min_refresh:
                result.add_issue(
                    issue_type="resource_refresh_too_fast",
                    severity=IssueSeverity.MEDIUM,
                    message=f"资源点 {node.get('node_id', 'unknown')} 的刷新间隔 {refresh_rate} 分钟低于区域资源等级 {resource_level} 的建议下限 {min_refresh} 分钟",
                    location=f"resource_nodes.{node.get('node_id', 'unknown')}.refresh_rate",
                    details={
                        "node_id": node.get("node_id"),
                        "refresh_rate": refresh_rate,
                        "resource_level": resource_level,
                        "min_refresh": min_refresh,
                    },
                )


def _estimate_quest_level(objective_count: int, exp: int) -> int:
    if exp <= 0:
        return 1

    level = 1
    exp_for_next_level = 100
    total_exp = 0

    while total_exp + exp_for_next_level <= exp and level < 100:
        total_exp += exp_for_next_level
        level += 1
        exp_for_next_level = int(exp_for_next_level * 1.2)

    return level
