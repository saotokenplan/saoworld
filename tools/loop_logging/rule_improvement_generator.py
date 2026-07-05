from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from .rule_evaluator import RuleEvaluationResult


@dataclass
class RuleImprovementIssue:
    issue_id: str
    rule_id: str
    rule_name: str
    issue_type: str
    change_type: str
    ts: datetime = field(default_factory=datetime.now)
    priority: str = "p1"
    context: Dict[str, Any] = field(default_factory=dict)
    observed_drift: Dict[str, Any] = field(default_factory=dict)
    proposed_change: Dict[str, Any] = field(default_factory=dict)
    acceptance: List[str] = field(default_factory=list)
    validation_data: List[Dict[str, Any]] = field(default_factory=list)
    risk: List[str] = field(default_factory=list)


class RuleImprovementGenerator:
    def __init__(self) -> None:
        pass

    def generate_improvement_issue(
        self, evaluation: RuleEvaluationResult, threshold_config: Dict[str, float]
    ) -> Optional[RuleImprovementIssue]:
        if not evaluation.needs_improvement:
            return None

        issue_id = f"RULE-{evaluation.rule_id.upper().replace('_', '-')}-{datetime.now().strftime('%Y%m%d')}"

        issue = RuleImprovementIssue(
            issue_id=issue_id,
            rule_id=evaluation.rule_id,
            rule_name=evaluation.rule_name,
            issue_type="rule_improvement",
            change_type=self._determine_change_type(evaluation),
            priority=self._determine_priority(evaluation),
            context=self._build_context(evaluation),
            observed_drift=self._build_drift(evaluation),
            proposed_change=self._build_proposed_change(evaluation, threshold_config),
            acceptance=self._build_acceptance(evaluation),
            validation_data=self._build_validation_data(evaluation),
            risk=self._build_risk(evaluation),
        )

        return issue

    def _determine_change_type(self, evaluation: RuleEvaluationResult) -> str:
        if evaluation.false_positive_rate > 0.3:
            return "调整阈值"
        if evaluation.false_negative_count > 0:
            return "新增规则"
        if evaluation.adoption_rate < 0.5:
            return "调整规则"
        return "新增样本"

    def _determine_priority(self, evaluation: RuleEvaluationResult) -> str:
        if evaluation.trend_drift_score > 0.3 or evaluation.false_positive_rate > 0.5:
            return "p0"
        if evaluation.needs_improvement:
            return "p1"
        return "p2"

    def _build_context(self, evaluation: RuleEvaluationResult) -> Dict[str, Any]:
        return {
            "rule_id": evaluation.rule_id,
            "rule_name": evaluation.rule_name,
            "total_issues": evaluation.total_issues,
            "evaluation_period": "last_30_days",
        }

    def _build_drift(self, evaluation: RuleEvaluationResult) -> Dict[str, Any]:
        drift_info: Dict[str, Any] = {}

        if evaluation.false_positive_rate > 0.3:
            drift_info["false_positive"] = {
                "rate": evaluation.false_positive_rate,
                "description": "规则误报率过高，产生了无效的 Gate Improvement Issue",
            }

        if evaluation.false_negative_count > 0:
            drift_info["false_negative"] = {
                "count": evaluation.false_negative_count,
                "description": "规则漏报了一些应该被检测到的门禁缺口",
            }

        if evaluation.trend_drift_score > 0.2:
            drift_info["trend_drift"] = {
                "score": evaluation.trend_drift_score,
                "description": "规则表现随时间变化明显，可能存在老化问题",
            }

        return drift_info

    def _build_proposed_change(
        self, evaluation: RuleEvaluationResult, threshold_config: Dict[str, float]
    ) -> Dict[str, Any]:
        change_type = self._determine_change_type(evaluation)
        change: Dict[str, Any] = {
            "change_type": change_type,
        }

        if change_type == "调整阈值":
            current_threshold = threshold_config.get("min_confidence", 0.7)
            new_threshold = min(0.9, current_threshold + 0.1)
            change.update({
                "rule_file": f"patterns/{evaluation.rule_id}.yaml",
                "threshold_file": "thresholds.yaml",
                "parameter": "confidence_threshold",
                "current_value": current_threshold,
                "proposed_value": new_threshold,
                "reason": f"当前误报率 {evaluation.false_positive_rate:.2f} 过高，建议提高置信度阈值",
            })

        elif change_type == "调整规则":
            change.update({
                "rule_file": f"patterns/{evaluation.rule_id}.yaml",
                "action": "优化匹配模式",
                "reason": f"当前采纳率 {evaluation.adoption_rate:.2f} 低于预期，建议优化规则匹配逻辑",
                "suggestions": [
                    "添加更多排除模式减少误报",
                    "细化匹配模式提高精准度",
                    "增加上下文条件判断",
                ],
            })

        elif change_type == "新增规则":
            change.update({
                "rule_file": f"patterns/{evaluation.rule_id}_v2.yaml",
                "action": "新增规则版本",
                "reason": f"存在 {evaluation.false_negative_count} 个漏报样本，需要新增规则覆盖",
                "suggestions": [
                    "分析漏报样本的共同特征",
                    "基于特征创建新规则",
                    "添加到 golden_cases 作为正例",
                ],
            })

        elif change_type == "新增样本":
            change.update({
                "sample_set": "golden_cases/",
                "action": "补充训练样本",
                "reason": "建议增加更多正例/反例样本提高规则质量",
                "suggestions": [
                    "从已接受的 Issue 中提取正例",
                    "从已拒绝的 Issue 中提取反例",
                    "确保样本多样性覆盖不同场景",
                ],
            })

        return change

    def _build_acceptance(self, evaluation: RuleEvaluationResult) -> List[str]:
        return [
            f"Issue 采纳率提升至 ≥ {self._get_target_adoption_rate(evaluation)}",
            f"无效 Issue 降低至 ≤ {self._get_target_false_positive_rate(evaluation)}",
            "偏差出现到提出 Issue 的平均时间 ≤ 24h",
        ]

    def _get_target_adoption_rate(self, evaluation: RuleEvaluationResult) -> float:
        return max(0.6, evaluation.adoption_rate + 0.1)

    def _get_target_false_positive_rate(self, evaluation: RuleEvaluationResult) -> float:
        return min(0.3, evaluation.false_positive_rate - 0.05)

    def _build_validation_data(self, evaluation: RuleEvaluationResult) -> List[Dict[str, Any]]:
        return [
            {"case": "positive", "rule_id": evaluation.rule_id, "expected_outcome": "应该被检测到"},
            {"case": "negative", "rule_id": evaluation.rule_id, "expected_outcome": "不应该被检测到"},
        ]

    def _build_risk(self, evaluation: RuleEvaluationResult) -> List[str]:
        risks: List[str] = []

        if self._determine_change_type(evaluation) == "调整阈值":
            risks.append("提高阈值可能导致漏报增加")
            risks.append("需要观察调整后的命中率变化")

        if evaluation.false_negative_count > 0:
            risks.append("新增规则可能与现有规则产生重叠")
            risks.append("需要确保规则之间的优先级合理")

        return risks

    def generate_all_improvement_issues(
        self, evaluations: List[RuleEvaluationResult], threshold_config: Dict[str, float]
    ) -> List[RuleImprovementIssue]:
        issues: List[RuleImprovementIssue] = []
        for evaluation in evaluations:
            issue = self.generate_improvement_issue(evaluation, threshold_config)
            if issue:
                issues.append(issue)
        return sorted(issues, key=lambda i: i.priority)