from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any

from .feedback_collector import IssueFeedbackCollector, IssueFeedback
from .golden_case_manager import GoldenCaseManager


@dataclass
class RuleEvaluationResult:
    rule_id: str
    rule_name: str
    total_issues: int = 0
    accepted_issues: int = 0
    rejected_issues: int = 0
    pending_issues: int = 0
    adoption_rate: float = 0.0
    false_positive_rate: float = 0.0
    false_negative_count: int = 0
    avg_latency_hours: float = 0.0
    avg_improvement_effect: float = 0.0
    avg_improvement_cost_hours: float = 0.0
    trend_drift_score: float = 0.0
    needs_improvement: bool = False
    improvement_reasons: List[str] = field(default_factory=list)


class RuleEvaluator:
    def __init__(
        self,
        feedback_collector: IssueFeedbackCollector,
        golden_case_manager: GoldenCaseManager,
        thresholds: Dict[str, float],
    ) -> None:
        self.feedback_collector: IssueFeedbackCollector = feedback_collector
        self.golden_case_manager: GoldenCaseManager = golden_case_manager
        self.thresholds: Dict[str, float] = thresholds

    def evaluate_rule(self, rule_id: str) -> RuleEvaluationResult:
        feedbacks = self.feedback_collector.get_feedbacks_by_rule_id(rule_id)
        golden_cases = self.golden_case_manager.get_cases_by_rule_id(rule_id)

        total_issues = len(feedbacks)
        accepted_issues = len([fb for fb in feedbacks if fb.acceptance == "accepted"])
        rejected_issues = len([fb for fb in feedbacks if fb.acceptance == "rejected"])
        pending_issues = len([fb for fb in feedbacks if fb.acceptance is None])

        adoption_rate = accepted_issues / total_issues if total_issues > 0 else 0.0
        false_positive_rate = rejected_issues / total_issues if total_issues > 0 else 0.0

        false_negative_count = self._calculate_false_negatives(golden_cases, feedbacks)
        avg_latency_hours = self._calculate_avg_latency(feedbacks)
        avg_improvement_effect = self._calculate_avg_effect(feedbacks)
        avg_improvement_cost_hours = self._calculate_avg_cost(feedbacks)
        trend_drift_score = self._calculate_trend_drift(feedbacks)

        needs_improvement, reasons = self._determine_needs_improvement(
            adoption_rate, false_positive_rate, false_negative_count, avg_latency_hours, trend_drift_score
        )

        result = RuleEvaluationResult(
            rule_id=rule_id,
            rule_name=self._get_rule_name(rule_id),
            total_issues=total_issues,
            accepted_issues=accepted_issues,
            rejected_issues=rejected_issues,
            pending_issues=pending_issues,
            adoption_rate=adoption_rate,
            false_positive_rate=false_positive_rate,
            false_negative_count=false_negative_count,
            avg_latency_hours=avg_latency_hours,
            avg_improvement_effect=avg_improvement_effect,
            avg_improvement_cost_hours=avg_improvement_cost_hours,
            trend_drift_score=trend_drift_score,
            needs_improvement=needs_improvement,
            improvement_reasons=reasons,
        )

        return result

    def _get_rule_name(self, rule_id: str) -> str:
        return rule_id.replace("_", " ").title()

    def _calculate_false_negatives(
        self, golden_cases: List[Any], feedbacks: List[IssueFeedback]
    ) -> int:
        case_signatures = set(case.failure_signature for case in golden_cases if case.case_type == "positive")
        feedback_signatures = set(fb.issue_type for fb in feedbacks)
        return len(case_signatures - feedback_signatures)

    def _calculate_avg_latency(self, feedbacks: List[IssueFeedback]) -> float:
        if not feedbacks:
            return 0.0

        total_latency = 0.0
        count = 0
        for fb in feedbacks:
            if fb.status == "completed":
                total_latency += fb.improvement_cost_hours or 0.0
                count += 1

        return total_latency / count if count > 0 else 0.0

    def _calculate_avg_effect(self, feedbacks: List[IssueFeedback]) -> float:
        effects = [fb.improvement_effect for fb in feedbacks if fb.improvement_effect is not None]
        return sum(effects) / len(effects) if effects else 0.0

    def _calculate_avg_cost(self, feedbacks: List[IssueFeedback]) -> float:
        costs = [fb.improvement_cost_hours for fb in feedbacks if fb.improvement_cost_hours is not None]
        return sum(costs) / len(costs) if costs else 0.0

    def _calculate_trend_drift(self, feedbacks: List[IssueFeedback]) -> float:
        if len(feedbacks) < 3:
            return 0.0

        accepted_recent = [
            fb for fb in feedbacks
            if fb.acceptance == "accepted" and fb.ts > datetime.now() - timedelta(days=14)
        ]
        rejected_recent = [
            fb for fb in feedbacks
            if fb.acceptance == "rejected" and fb.ts > datetime.now() - timedelta(days=14)
        ]

        accepted_old = [
            fb for fb in feedbacks
            if fb.acceptance == "accepted" and fb.ts <= datetime.now() - timedelta(days=14)
        ]
        rejected_old = [
            fb for fb in feedbacks
            if fb.acceptance == "rejected" and fb.ts <= datetime.now() - timedelta(days=14)
        ]

        rate_recent = (
            len(accepted_recent) / (len(accepted_recent) + len(rejected_recent))
            if (len(accepted_recent) + len(rejected_recent)) > 0
            else 0.5
        )
        rate_old = (
            len(accepted_old) / (len(accepted_old) + len(rejected_old))
            if (len(accepted_old) + len(rejected_old)) > 0
            else 0.5
        )

        return abs(rate_recent - rate_old)

    def _determine_needs_improvement(
        self,
        adoption_rate: float,
        false_positive_rate: float,
        false_negative_count: int,
        avg_latency_hours: float,
        trend_drift_score: float,
    ) -> tuple[bool, List[str]]:
        reasons: List[str] = []
        needs_improvement = False

        min_adoption_rate = self.thresholds.get("min_issue_adoption_rate", 0.6)
        max_false_positive_rate = self.thresholds.get("max_false_positive_rate", 0.35)
        max_latency_hours = self.thresholds.get("max_latency_hours", 24)
        alert_threshold = self.thresholds.get("alert_threshold", 0.2)

        if adoption_rate < min_adoption_rate:
            reasons.append(f"采纳率 {adoption_rate:.2f} 低于阈值 {min_adoption_rate}")
            needs_improvement = True

        if false_positive_rate > max_false_positive_rate:
            reasons.append(f"误报率 {false_positive_rate:.2f} 高于阈值 {max_false_positive_rate}")
            needs_improvement = True

        if false_negative_count > 0:
            reasons.append(f"存在 {false_negative_count} 个漏报样本")
            needs_improvement = True

        if avg_latency_hours > max_latency_hours:
            reasons.append(f"平均延迟 {avg_latency_hours:.2f}h 高于阈值 {max_latency_hours}h")
            needs_improvement = True

        if trend_drift_score > alert_threshold:
            reasons.append(f"规则漂移分数 {trend_drift_score:.2f} 高于阈值 {alert_threshold}")
            needs_improvement = True

        return needs_improvement, reasons

    def evaluate_all_rules(self) -> List[RuleEvaluationResult]:
        all_rules = set(fb.rule_id for fb in self.feedback_collector.feedbacks.values())
        results = []
        for rule_id in all_rules:
            result = self.evaluate_rule(rule_id)
            results.append(result)
        return sorted(results, key=lambda r: r.adoption_rate)
