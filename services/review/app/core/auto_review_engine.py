"""自动审核规则引擎模块。"""

import logging
from typing import Any

from app.core.metrics import record_rule_decision

logger = logging.getLogger(__name__)


class AutoReviewRule:
    """自动审核规则基类。"""

    def evaluate(self, object_type: str, object_payload: dict[str, Any], quality_score: float | None) -> str | None:
        """评估规则，返回审核结果或None（不适用）。

        Returns:
            "approved", "rejected", "manual_review", or None
        """
        raise NotImplementedError


class QualityScoreRule(AutoReviewRule):
    """基于质量分数的自动审核规则。"""

    def __init__(self, approve_threshold: float = 0.8, reject_threshold: float = 0.5):
        self.approve_threshold = approve_threshold
        self.reject_threshold = reject_threshold

    def evaluate(self, object_type: str, object_payload: dict[str, Any], quality_score: float | None) -> str | None:
        if quality_score is None:
            return None

        if quality_score >= self.approve_threshold:
            return "approved"
        if quality_score < self.reject_threshold:
            return "rejected"
        return None


class ContentSafetyRule(AutoReviewRule):
    """基于内容安全的自动审核规则。"""

    SENSITIVE_PATTERNS = [
        "暴力",
        "血腥",
        "色情",
        "毒品",
        "赌博",
        "恐怖",
        "邪教",
        "仇恨",
        "歧视",
        "自杀",
        "自残",
    ]

    HIGH_RISK_PATTERNS = [
        "死亡",
        "屠杀",
        "毁灭",
        "灾难",
        "瘟疫",
        "战争",
    ]

    def evaluate(self, object_type: str, object_payload: dict[str, Any], quality_score: float | None) -> str | None:
        text_content = self._extract_text_content(object_payload)

        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in text_content:
                logger.warning(f"Sensitive content detected: {pattern}")
                return "rejected"

        for pattern in self.HIGH_RISK_PATTERNS:
            if pattern in text_content:
                logger.info(f"High-risk content detected: {pattern}, requiring manual review")
                return "manual_review"

        return None

    def _extract_text_content(self, payload: dict[str, Any]) -> str:
        """提取所有文本内容用于检测。"""
        texts: list[str] = []

        def collect_text(obj: Any) -> None:
            if isinstance(obj, str):
                texts.append(obj)
            elif isinstance(obj, dict):
                for value in obj.values():
                    collect_text(value)
            elif isinstance(obj, list):
                for item in obj:
                    collect_text(item)

        collect_text(payload)
        return " ".join(texts)


class FieldCompletenessRule(AutoReviewRule):
    """基于字段完整性的自动审核规则。"""

    REQUIRED_FIELDS_BY_TYPE = {
        "npc": ["npc_key", "name", "role", "description", "personality"],
        "quest": ["quest_key", "title", "description", "quest_type", "objectives"],
        "region": ["region_key", "name", "description", "danger_level", "recommended_level"],
        "settlement": ["settlement_key", "name", "settlement_type", "description"],
        "monster": ["monster_key", "name", "monster_type", "level", "hp", "attack"],
        "boss": ["monster_key", "name", "level", "hp", "attack", "phase_count"],
        "item": ["item_key", "item_type", "name", "rarity", "level_requirement"],
    }

    def __init__(self, min_completeness: float = 0.85):
        self.min_completeness = min_completeness

    def evaluate(self, object_type: str, object_payload: dict[str, Any], quality_score: float | None) -> str | None:
        required_fields = self.REQUIRED_FIELDS_BY_TYPE.get(object_type, [])
        if not required_fields:
            return None

        missing = []
        for field in required_fields:
            value = object_payload.get(field)
            if value is None:
                missing.append(field)
            elif isinstance(value, str) and not value.strip():
                missing.append(field)

        completeness = (len(required_fields) - len(missing)) / len(required_fields)

        if completeness < self.min_completeness:
            logger.warning(f"Field completeness {completeness:.2%} below threshold for {object_type}")
            return "rejected"

        return None


class DuplicateDetectionRule(AutoReviewRule):
    """基于重复度检测的自动审核规则。

    `max_similarity` 为可调度阈值（默认 0.8），表示「自相似度」上限：
    当 description 的字符自相似度 >= max_similarity 时判 rejected。
    自相似度以 `1 - 字符多样度` 近似，作为单对象内重复 / 低质文本的快速拦截；
    跨样本相似度（WP2 场景 D 改造项）由 `cross_similarity` 提供纯函数能力，
    待运行时语料注入引擎后接线，当前 `evaluate` 仅使用单对象自相似度口径。
    """

    def __init__(self, max_similarity: float = 0.8):
        self.max_similarity = max_similarity

    @staticmethod
    def self_similarity(description: str) -> float:
        """单对象内自相似度近似：1 - 字符多样度。

        字符越单一（重复 / 堆砌），自相似度越高，越接近 1.0；空串返回 0.0。
        """
        text = str(description)
        total = len(text)
        if total == 0:
            return 0.0
        diversity = len(set(text)) / total
        return 1.0 - diversity

    @staticmethod
    def cross_similarity(a: str, b: str) -> float:
        """两个文本的字符级 Jaccard 相似度，用于跨样本重复检测。

        返回 0.0~1.0；任意一方为空串返回 0.0。
        """
        set_a = set(str(a))
        set_b = set(str(b))
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)

    def evaluate(self, object_type: str, object_payload: dict[str, Any], quality_score: float | None) -> str | None:
        description = str(object_payload.get("description", ""))
        if len(description) < 20:
            return None

        similarity = self.self_similarity(description)
        if similarity >= self.max_similarity:
            logger.warning(f"High self-similarity detected: {similarity:.2f} >= {self.max_similarity:.2f}")
            return "rejected"

        return None


class AutoReviewEngine:
    """自动审核规则引擎。"""

    def __init__(self, rules: list[AutoReviewRule] | None = None):
        if rules is None:
            rules = [
                ContentSafetyRule(),
                FieldCompletenessRule(),
                DuplicateDetectionRule(),
                QualityScoreRule(),
            ]
        self.rules = rules

    def evaluate(self, object_type: str, object_payload: dict[str, Any], quality_score: float | None) -> dict[str, Any]:
        """评估所有规则，返回自动审核结果。"""
        results = []
        final_result: str | None = None
        reason: str = ""

        for rule in self.rules:
            try:
                result = rule.evaluate(object_type, object_payload, quality_score)
                rule_name = rule.__class__.__name__
                results.append({"rule": rule_name, "result": result})

                # M4: 规则归因埋点（规则不适用记 not_applied，用于 A3 归因面板）
                record_rule_decision(rule_name, result if result is not None else "not_applied")

                if result is not None and final_result is None:
                    final_result = result
                    if result == "approved":
                        reason = f"Automatic approval by {rule_name}"
                    elif result == "rejected":
                        reason = f"Automatic rejection by {rule_name}"
                    elif result == "manual_review":
                        reason = f"Requires manual review per {rule_name}"
            except Exception as e:
                logger.error(f"Rule evaluation failed: {rule.__class__.__name__}, error: {e}")
                results.append({"rule": rule.__class__.__name__, "result": None, "error": str(e)})
                record_rule_decision(rule_name, "error")

        if final_result is None:
            final_result = "manual_review"
            reason = "No automatic decision, requires manual review"

        return {
            "auto_result": final_result,
            "reason": reason,
            "rule_results": results,
            "is_automatic": final_result != "manual_review",
        }


auto_review_engine = AutoReviewEngine()