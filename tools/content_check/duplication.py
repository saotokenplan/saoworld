from typing import Any

from .base import BaseChecker, CheckResult, CheckStatus, IssueSeverity


class DuplicationChecker(BaseChecker):
    name = "duplication"

    def check(self, content_data: dict[str, Any], context: dict[str, Any] | None = None) -> CheckResult:
        context = context or {}
        result = CheckResult(
            check_name=self.name,
            status=CheckStatus.PASSED,
            score=100.0,
        )

        existing_content = context.get("existing_content", {})

        self._check_npc_similarity(content_data, existing_content, result)
        self._check_quest_skeleton_reuse(content_data, existing_content, result)
        self._check_text_paragraph_repeat(content_data, existing_content, result)
        self._check_internal_duplication(content_data, result)

        result.score = self._calculate_score(result.issues)
        result.status = self._determine_status(result.score, result.issues)

        return result

    def _check_npc_similarity(
        self, content_data: dict[str, Any], existing_content: dict[str, Any], result: CheckResult
    ) -> None:
        threshold = self.config.get("npc_similarity_threshold", 0.8)
        if threshold >= 1.0:
            return

        new_npcs = content_data.get("npcs", [])
        existing_npcs = existing_content.get("npcs", [])

        all_npcs = existing_npcs + new_npcs

        for i, npc1 in enumerate(all_npcs):
            for j, npc2 in enumerate(all_npcs):
                if j <= i:
                    continue

                npc1_id = npc1.get("npc_id", f"npc_{i}")
                npc2_id = npc2.get("npc_id", f"npc_{j}")

                similarity = _calculate_npc_similarity(npc1, npc2)
                if similarity >= threshold:
                    result.add_issue(
                        issue_type="npc_similarity_too_high",
                        severity=IssueSeverity.MEDIUM,
                        message=f"NPC {npc1.get('name', npc1_id)} 与 {npc2.get('name', npc2_id)} 的设定相似度 {similarity:.2f} 超过阈值 {threshold}",
                        location=f"npcs.{npc1_id} <-> npcs.{npc2_id}",
                        details={
                            "npc1_id": npc1_id,
                            "npc2_id": npc2_id,
                            "similarity": similarity,
                            "threshold": threshold,
                        },
                    )

    def _check_quest_skeleton_reuse(
        self, content_data: dict[str, Any], existing_content: dict[str, Any], result: CheckResult
    ) -> None:
        threshold = self.config.get("quest_skeleton_reuse_threshold", 0.6)
        if threshold >= 1.0:
            return

        new_quests = content_data.get("quests", [])
        existing_quests = existing_content.get("quests", [])

        all_quests = existing_quests + new_quests

        for i, quest1 in enumerate(all_quests):
            for j, quest2 in enumerate(all_quests):
                if j <= i:
                    continue

                quest1_id = quest1.get("quest_id", f"quest_{i}")
                quest2_id = quest2.get("quest_id", f"quest_{j}")

                similarity = _calculate_quest_skeleton_similarity(quest1, quest2)
                if similarity >= threshold:
                    result.add_issue(
                        issue_type="quest_skeleton_reuse_too_high",
                        severity=IssueSeverity.MEDIUM,
                        message=f"任务 {quest1.get('title', quest1_id)} 与 {quest2.get('title', quest2_id)} 的骨架复用率 {similarity:.2f} 超过阈值 {threshold}",
                        location=f"quests.{quest1_id} <-> quests.{quest2_id}",
                        details={
                            "quest1_id": quest1_id,
                            "quest2_id": quest2_id,
                            "similarity": similarity,
                            "threshold": threshold,
                        },
                    )

    def _check_text_paragraph_repeat(
        self, content_data: dict[str, Any], existing_content: dict[str, Any], result: CheckResult
    ) -> None:
        threshold = self.config.get("text_paragraph_repeat_threshold", 0.3)
        min_length = self.config.get("min_text_length_for_check", 20)
        if threshold >= 1.0:
            return

        new_texts = _extract_text_paragraphs(content_data, min_length)
        existing_texts = _extract_text_paragraphs(existing_content, min_length)

        all_texts = existing_texts + new_texts

        for i, (loc1, text1) in enumerate(all_texts):
            for j, (loc2, text2) in enumerate(all_texts):
                if j <= i:
                    continue

                similarity = _calculate_text_similarity(text1, text2)
                if similarity >= threshold:
                    result.add_issue(
                        issue_type="text_paragraph_repeat_too_high",
                        severity=IssueSeverity.LOW,
                        message=f"文本段落重复率 {similarity:.2f} 超过阈值 {threshold}",
                        location=f"{loc1} <-> {loc2}",
                        details={
                            "text1_location": loc1,
                            "text2_location": loc2,
                            "similarity": similarity,
                            "threshold": threshold,
                        },
                    )

    def _check_internal_duplication(self, content_data: dict[str, Any], result: CheckResult) -> None:
        npcs = content_data.get("npcs", [])
        npc_ids = [n.get("npc_id") for n in npcs if n.get("npc_id")]

        if len(npc_ids) != len(set(npc_ids)):
            duplicate_ids = [nid for nid in npc_ids if npc_ids.count(nid) > 1]
            for dup_id in set(duplicate_ids):
                result.add_issue(
                    issue_type="duplicate_npc_id",
                    severity=IssueSeverity.HIGH,
                    message=f"NPC ID 重复: {dup_id}",
                    location=f"npcs.{dup_id}",
                    details={"npc_id": dup_id},
                )

        quests = content_data.get("quests", [])
        quest_ids = [q.get("quest_id") for q in quests if q.get("quest_id")]

        if len(quest_ids) != len(set(quest_ids)):
            duplicate_ids = [qid for qid in quest_ids if quest_ids.count(qid) > 1]
            for dup_id in set(duplicate_ids):
                result.add_issue(
                    issue_type="duplicate_quest_id",
                    severity=IssueSeverity.HIGH,
                    message=f"任务 ID 重复: {dup_id}",
                    location=f"quests.{dup_id}",
                    details={"quest_id": dup_id},
                )


def _calculate_npc_similarity(npc1: dict[str, Any], npc2: dict[str, Any]) -> float:
    score = 0.0
    total = 0.0

    if npc1.get("faction") and npc2.get("faction"):
        total += 1
        if npc1["faction"] == npc2["faction"]:
            score += 1

    if npc1.get("role") and npc2.get("role"):
        total += 1
        if npc1["role"] == npc2["role"]:
            score += 1

    p1 = set(npc1.get("personality", []))
    p2 = set(npc2.get("personality", []))
    if p1 and p2:
        total += 1
        intersection = p1 & p2
        union = p1 | p2
        score += len(intersection) / len(union) if union else 0

    d1 = npc1.get("description", "")
    d2 = npc2.get("description", "")
    if d1 and d2:
        total += 2
        score += 2 * _calculate_text_similarity(d1, d2)

    return score / total if total > 0 else 0.0


def _calculate_quest_skeleton_similarity(quest1: dict[str, Any], quest2: dict[str, Any]) -> float:
    score = 0.0
    total = 0.0

    if quest1.get("type") and quest2.get("type"):
        total += 0.5
        if quest1["type"] == quest2["type"]:
            score += 0.5

    obj1 = quest1.get("objectives", [])
    obj2 = quest2.get("objectives", [])
    if obj1 and obj2:
        total += 1
        types1 = {o.get("type") for o in obj1 if o.get("type")}
        types2 = {o.get("type") for o in obj2 if o.get("type")}
        if types1 and types2:
            intersection = types1 & types2
            union = types1 | types2
            score += len(intersection) / len(union) if union else 0

    r1 = quest1.get("region")
    r2 = quest2.get("region")
    if r1 and r2:
        total += 0.5
        if r1 == r2:
            score += 0.5

    pre1 = set(quest1.get("prerequisites", []))
    pre2 = set(quest2.get("prerequisites", []))
    if pre1 and pre2:
        total += 0.5
        intersection = pre1 & pre2
        union = pre1 | pre2
        score += 0.5 * (len(intersection) / len(union) if union else 0)

    return score / total if total > 0 else 0.0


def _calculate_text_similarity(text1: str, text2: str) -> float:
    if not text1 or not text2:
        return 0.0

    words1 = set(_tokenize(text1))
    words2 = set(_tokenize(text2))

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union) if union else 0.0


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    current = ""
    for char in text:
        if char.isalnum() or "\u4e00" <= char <= "\u9fff":
            current += char
        else:
            if current:
                tokens.append(current.lower())
                current = ""
    if current:
        tokens.append(current.lower())
    return tokens


def _extract_text_paragraphs(data: Any, min_length: int, prefix: str = "") -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []

    if isinstance(data, dict):
        for key, value in data.items():
            current_prefix = f"{prefix}.{key}" if prefix else key
            result.extend(_extract_text_paragraphs(value, min_length, current_prefix))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            current_prefix = f"{prefix}[{i}]"
            result.extend(_extract_text_paragraphs(item, min_length, current_prefix))
    elif isinstance(data, str):
        if len(data) >= min_length:
            result.append((prefix, data))

    return result
