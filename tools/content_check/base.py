from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IssueSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CheckStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


@dataclass
class CheckIssue:
    issue_type: str
    severity: IssueSeverity
    message: str
    location: str | None = None
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "issue_type": self.issue_type,
            "severity": self.severity.value,
            "message": self.message,
        }
        if self.location:
            result["location"] = self.location
        if self.details:
            result["details"] = self.details
        return result


@dataclass
class CheckResult:
    check_name: str
    status: CheckStatus
    score: float
    issues: list[CheckIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == CheckStatus.PASSED

    @property
    def issues_count(self) -> int:
        return len(self.issues)

    @property
    def critical_issues(self) -> list[CheckIssue]:
        return [i for i in self.issues if i.severity == IssueSeverity.CRITICAL]

    @property
    def high_issues(self) -> list[CheckIssue]:
        return [i for i in self.issues if i.severity == IssueSeverity.HIGH]

    def add_issue(
        self,
        issue_type: str,
        severity: IssueSeverity,
        message: str,
        location: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.issues.append(CheckIssue(
            issue_type=issue_type,
            severity=severity,
            message=message,
            location=location,
            details=details,
        ))

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_name": self.check_name,
            "status": self.status.value,
            "score": self.score,
            "issues_count": self.issues_count,
            "critical_issues_count": len(self.critical_issues),
            "high_issues_count": len(self.high_issues),
            "issues": [i.to_dict() for i in self.issues],
        }


class BaseChecker:
    name: str = "base"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    def check(self, content_data: dict[str, Any], context: dict[str, Any] | None = None) -> CheckResult:
        raise NotImplementedError

    def _calculate_score(self, issues: list[CheckIssue]) -> float:
        if not issues:
            return 100.0

        total_weight = 0
        for issue in issues:
            if issue.severity == IssueSeverity.CRITICAL:
                total_weight += 25
            elif issue.severity == IssueSeverity.HIGH:
                total_weight += 15
            elif issue.severity == IssueSeverity.MEDIUM:
                total_weight += 8
            else:
                total_weight += 3

        return max(0.0, 100.0 - total_weight)

    def _determine_status(self, score: float, issues: list[CheckIssue]) -> CheckStatus:
        if any(i.severity == IssueSeverity.CRITICAL for i in issues):
            return CheckStatus.FAILED
        if score >= 75:
            return CheckStatus.PASSED
        if score >= 50:
            return CheckStatus.NEEDS_REVIEW
        return CheckStatus.FAILED
