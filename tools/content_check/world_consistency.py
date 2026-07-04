from typing import Any

from .base import BaseChecker, CheckResult, CheckStatus, IssueSeverity


class WorldConsistencyChecker(BaseChecker):
    name = "world_consistency"

    def check(self, content_data: dict[str, Any], context: dict[str, Any] | None = None) -> CheckResult:
        context = context or {}
        result = CheckResult(
            check_name=self.name,
            status=CheckStatus.PASSED,
            score=100.0,
        )

        self._check_schema_version(content_data, result)
        self._check_faction_relations(content_data, context, result)
        self._check_chapter_boundaries(content_data, context, result)
        self._check_resource_matching(content_data, context, result)
        self._check_mainline_protection(content_data, context, result)

        result.score = self._calculate_score(result.issues)
        result.status = self._determine_status(result.score, result.issues)

        return result

    def _check_schema_version(self, content_data: dict[str, Any], result: CheckResult) -> None:
        if not self.config.get("schema_version_required", True):
            return

        if "schema_version" not in content_data:
            result.add_issue(
                issue_type="missing_schema_version",
                severity=IssueSeverity.HIGH,
                message="内容缺少 schema_version 字段",
                location="root",
            )
            return

        schema_version = content_data["schema_version"]
        if not isinstance(schema_version, int) or schema_version < 1:
            result.add_issue(
                issue_type="invalid_schema_version",
                severity=IssueSeverity.HIGH,
                message=f"schema_version 无效: {schema_version}，必须为正整数",
                location="root.schema_version",
                details={"schema_version": schema_version},
            )

    def _check_faction_relations(
        self, content_data: dict[str, Any], context: dict[str, Any], result: CheckResult
    ) -> None:
        if not self.config.get("faction_relation_check", True):
            return

        world_factions = context.get("factions", {})
        world_relations = context.get("faction_relations", [])

        if not world_factions:
            return

        npcs = content_data.get("npcs", [])
        for npc in npcs:
            npc_faction = npc.get("faction")
            if not npc_faction:
                continue

            if npc_faction not in world_factions:
                result.add_issue(
                    issue_type="unknown_faction",
                    severity=IssueSeverity.MEDIUM,
                    message=f"NPC {npc.get('name', npc.get('npc_id'))} 所属阵营 {npc_faction} 不存在于世界观设定中",
                    location=f"npcs.{npc.get('npc_id', 'unknown')}.faction",
                    details={"npc_id": npc.get("npc_id"), "faction": npc_faction},
                )

        quests = content_data.get("quests", [])
        for quest in quests:
            rewards = quest.get("rewards", {})
            reputation = rewards.get("reputation", {})
            for faction_id in reputation:
                if faction_id not in world_factions:
                    result.add_issue(
                        issue_type="unknown_faction_in_rewards",
                        severity=IssueSeverity.MEDIUM,
                        message=f"任务 {quest.get('title', quest.get('quest_id'))} 的声望奖励包含未知阵营 {faction_id}",
                        location=f"quests.{quest.get('quest_id', 'unknown')}.rewards.reputation",
                        details={"quest_id": quest.get("quest_id"), "faction": faction_id},
                    )

        if not world_relations:
            return

    def _check_chapter_boundaries(
        self, content_data: dict[str, Any], context: dict[str, Any], result: CheckResult
    ) -> None:
        if not self.config.get("chapter_boundary_check", True):
            return

        chapters = context.get("chapters", {})
        if not chapters:
            return

        chapter_ids = {c.get("chapter_id") for c in chapters}

        quests = content_data.get("quests", [])
        for quest in quests:
            quest_chapter = quest.get("chapter")
            if quest_chapter and quest_chapter not in chapter_ids:
                result.add_issue(
                    issue_type="quest_outside_chapter",
                    severity=IssueSeverity.MEDIUM,
                    message=f"任务 {quest.get('title', quest.get('quest_id'))} 所属章节 {quest_chapter} 不存在",
                    location=f"quests.{quest.get('quest_id', 'unknown')}.chapter",
                    details={"quest_id": quest.get("quest_id"), "chapter": quest_chapter},
                )

            prerequisites = quest.get("prerequisites", [])
            for prereq in prerequisites:
                if not _is_valid_prereq(prereq, quests, chapter_ids):
                    result.add_issue(
                        issue_type="invalid_prerequisite",
                        severity=IssueSeverity.HIGH,
                        message=f"任务 {quest.get('title', quest.get('quest_id'))} 的前置任务 {prereq} 无效",
                        location=f"quests.{quest.get('quest_id', 'unknown')}.prerequisites",
                        details={"quest_id": quest.get("quest_id"), "prerequisite": prereq},
                    )

    def _check_resource_matching(
        self, content_data: dict[str, Any], context: dict[str, Any], result: CheckResult
    ) -> None:
        if not self.config.get("resource_matching_check", True):
            return

        regions = context.get("regions", {})
        if not regions:
            return

        quests = content_data.get("quests", [])
        for quest in quests:
            region_id = quest.get("region")
            if not region_id or region_id not in regions:
                continue

            region = regions[region_id]
            level_range = region.get("level_range", [0, 999])
            rewards = quest.get("rewards", {})
            exp = rewards.get("experience", 0)

            min_level, max_level = level_range
            expected_max_exp = max_level * 50

            if exp > expected_max_exp * 2:
                result.add_issue(
                    issue_type="exp_reward_mismatch",
                    severity=IssueSeverity.MEDIUM,
                    message=f"任务 {quest.get('title', quest.get('quest_id'))} 的经验奖励 {exp} 与区域等级 {level_range} 不匹配",
                    location=f"quests.{quest.get('quest_id', 'unknown')}.rewards.experience",
                    details={
                        "quest_id": quest.get("quest_id"),
                        "experience": exp,
                        "region_level_range": level_range,
                        "expected_max": expected_max_exp,
                    },
                )

            risk_level = region.get("risk_level", "low")
            gold = rewards.get("gold", 0)
            max_gold_by_risk = {
                "low": 50,
                "low_to_medium": 100,
                "medium": 150,
                "medium_to_high": 250,
                "high": 400,
            }
            max_gold = max_gold_by_risk.get(risk_level, 100)
            if gold > max_gold:
                result.add_issue(
                    issue_type="gold_reward_mismatch",
                    severity=IssueSeverity.LOW,
                    message=f"任务 {quest.get('title', quest.get('quest_id'))} 的金币奖励 {gold} 超过区域风险等级 {risk_level} 的建议上限 {max_gold}",
                    location=f"quests.{quest.get('quest_id', 'unknown')}.rewards.gold",
                    details={
                        "quest_id": quest.get("quest_id"),
                        "gold": gold,
                        "risk_level": risk_level,
                        "max_gold": max_gold,
                    },
                )

    def _check_mainline_protection(
        self, content_data: dict[str, Any], context: dict[str, Any], result: CheckResult
    ) -> None:
        if not self.config.get("mainline_protection", True):
            return

        protected_elements = context.get("protected_mainline_elements", set())
        if not protected_elements:
            return

        npcs = content_data.get("npcs", [])
        for npc in npcs:
            npc_id = npc.get("npc_id")
            if npc_id in protected_elements:
                if "description" in npc or "dialogues" in npc:
                    result.add_issue(
                        issue_type="mainline_npc_modified",
                        severity=IssueSeverity.CRITICAL,
                        message=f"主线关键 NPC {npc.get('name', npc_id)} 被修改，可能影响主线剧情",
                        location=f"npcs.{npc_id}",
                        details={"npc_id": npc_id, "protected": True},
                    )

        quests = content_data.get("quests", [])
        for quest in quests:
            quest_id = quest.get("quest_id")
            quest_type = quest.get("type", "side")
            if quest_type == "main" and quest_id in protected_elements:
                result.add_issue(
                    issue_type="mainline_quest_modified",
                    severity=IssueSeverity.CRITICAL,
                    message=f"主线任务 {quest.get('title', quest_id)} 被修改，可能影响主线终局",
                    location=f"quests.{quest_id}",
                    details={"quest_id": quest_id, "protected": True},
                )


def _is_valid_prereq(prereq: str, quests: list[dict[str, Any]], chapter_ids: set[str]) -> bool:
    quest_ids = {q.get("quest_id") for q in quests}
    if prereq in quest_ids:
        return True

    if prereq.startswith("chapter_"):
        return prereq in chapter_ids

    return False
