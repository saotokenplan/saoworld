from typing import Any

from .base import BaseChecker, CheckResult, CheckStatus, IssueSeverity


class ContentSafetyChecker(BaseChecker):
    name = "content_safety"

    def check(self, content_data: dict[str, Any], context: dict[str, Any] | None = None) -> CheckResult:
        result = CheckResult(
            check_name=self.name,
            status=CheckStatus.PASSED,
            score=100.0,
        )

        all_text = _extract_all_text(content_data)

        self._check_banned_words(all_text, result)
        self._check_high_risk_topics(all_text, result)
        self._check_age_rating(content_data, all_text, result)
        self._check_violence_content(all_text, result)

        result.score = self._calculate_score(result.issues)
        result.status = self._determine_status(result.score, result.issues)

        return result

    def _check_banned_words(self, all_text: list[tuple[str, str]], result: CheckResult) -> None:
        banned_words = self.config.get("banned_words", [])
        if not banned_words:
            return

        max_banned = self.config.get("max_banned_words_per_content", 0)
        banned_count = 0

        for location, text in all_text:
            for word in banned_words:
                if word in text:
                    banned_count += 1
                    result.add_issue(
                        issue_type="banned_word_found",
                        severity=IssueSeverity.CRITICAL,
                        message=f"内容包含违禁词: {word}",
                        location=location,
                        details={"banned_word": word},
                    )

        if max_banned > 0 and banned_count > max_banned:
            result.add_issue(
                issue_type="banned_word_threshold_exceeded",
                severity=IssueSeverity.CRITICAL,
                message=f"违禁词命中次数超过阈值: {banned_count}/{max_banned}",
                details={"banned_count": banned_count, "max_banned_words_per_content": max_banned},
            )

    def _check_high_risk_topics(self, all_text: list[tuple[str, str]], result: CheckResult) -> None:
        high_risk_topics = self.config.get("high_risk_topics", [])
        if not high_risk_topics:
            return

        for location, text in all_text:
            for topic in high_risk_topics:
                if topic in text:
                    result.add_issue(
                        issue_type="high_risk_topic",
                        severity=IssueSeverity.HIGH,
                        message=f"内容涉及高风险主题: {topic}，需要人工复核",
                        location=location,
                        details={"risk_topic": topic},
                    )

    def _check_age_rating(
        self, content_data: dict[str, Any], all_text: list[tuple[str, str]], result: CheckResult
    ) -> None:
        target_age_rating = self.config.get("target_age_rating", "teen")
        severity = IssueSeverity.HIGH if target_age_rating == "all" else IssueSeverity.MEDIUM

        mature_themes = [
            "死亡",
            "血腥",
            "恐怖",
            "惊悚",
            "诅咒",
            "献祭",
            "折磨",
            "屠杀",
        ]

        mature_count = 0
        for location, text in all_text:
            for theme in mature_themes:
                if theme in text:
                    mature_count += 1
                    if mature_count <= 5:
                        result.add_issue(
                            issue_type="mature_theme",
                            severity=severity,
                            message=f"内容包含成人向主题元素: {theme}",
                            location=location,
                            details={"theme": theme},
                        )
                    break

    def _check_violence_content(self, all_text: list[tuple[str, str]], result: CheckResult) -> None:
        extreme_violence = [
            "虐杀",
            "分尸",
            "凌迟",
            "腰斩",
            "活埋",
            "烧死",
        ]

        for location, text in all_text:
            for keyword in extreme_violence:
                if keyword in text:
                    result.add_issue(
                        issue_type="extreme_violence",
                        severity=IssueSeverity.CRITICAL,
                        message=f"内容包含极端暴力描述: {keyword}",
                        location=location,
                        details={"keyword": keyword},
                    )


def _extract_all_text(content_data: dict[str, Any], prefix: str = "") -> list[tuple[str, str]]:
    texts: list[tuple[str, str]] = []

    if isinstance(content_data, dict):
        for key, value in content_data.items():
            current_prefix = f"{prefix}.{key}" if prefix else key
            texts.extend(_extract_all_text(value, current_prefix))
    elif isinstance(content_data, list):
        for i, item in enumerate(content_data):
            current_prefix = f"{prefix}[{i}]"
            texts.extend(_extract_all_text(item, current_prefix))
    elif isinstance(content_data, str):
        if len(content_data) >= 5:
            texts.append((prefix, content_data))

    return texts
