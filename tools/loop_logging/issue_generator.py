from __future__ import annotations

from typing import List, Dict, Any, Optional

from .schema import (
    GateImprovementIssue,
    GapType,
    GateType,
    GateTrigger,
)
from .clusterer import FailureCluster


class GateImprovementIssueGenerator:
    ERROR_TYPE_TO_GATE_TYPE: Dict[str, GateType] = {
        "mypy": GateType.STATIC,
        "ruff": GateType.STATIC,
        "lint": GateType.STATIC,
        "typecheck": GateType.STATIC,
        "pytest": GateType.UNIT,
        "test": GateType.UNIT,
        "assertion": GateType.UNIT,
        "attr-error": GateType.UNIT,
        "type-error": GateType.UNIT,
        "value-error": GateType.UNIT,
        "key-error": GateType.UNIT,
        "index-error": GateType.UNIT,
        "world-rule": GateType.CONTENT,
        "reward-budget": GateType.CONTENT,
        "safety-rule": GateType.CONTENT,
        "duplication-rule": GateType.CONTENT,
        "runtime-error": GateType.INTEGRATION,
        "conn-error": GateType.INTEGRATION,
        "timeout-error": GateType.INTEGRATION,
    }

    ERROR_TYPE_TO_RISK_COVERAGE: Dict[str, List[str]] = {
        "mypy": ["type-safety"],
        "ruff": ["style", "regression"],
        "lint": ["style", "regression"],
        "typecheck": ["type-safety", "regression"],
        "pytest": ["regression", "data-integrity"],
        "test": ["regression"],
        "assertion": ["regression", "data-integrity"],
        "attr-error": ["regression", "data-integrity"],
        "type-error": ["type-safety", "regression"],
        "value-error": ["data-integrity"],
        "key-error": ["data-integrity"],
        "index-error": ["data-integrity"],
        "world-rule": ["world-consistency"],
        "reward-budget": ["reward-boundary"],
        "safety-rule": ["content-safety"],
        "duplication-rule": ["duplication"],
        "runtime-error": ["crash", "regression"],
        "conn-error": ["crash"],
        "timeout-error": ["performance"],
    }

    def __init__(self) -> None:
        self._issue_counter = 0

    def generate_issue(
        self,
        cluster: FailureCluster,
        gap_type: GapType,
        evidence: Optional[List[Dict[str, Any]]] = None,
    ) -> GateImprovementIssue:
        symptom = self._generate_symptom(cluster)
        root_cause = self._generate_root_cause(cluster, gap_type)
        gate_type = self._determine_gate_type(cluster)
        gate_name = self._generate_gate_name(cluster, gap_type)
        trigger = self._determine_trigger(cluster)
        command = self._generate_command(cluster, gate_type)
        risk_coverage = self._determine_risk_coverage(cluster)
        acceptance = self._generate_acceptance(cluster, gap_type)
        priority = self._determine_priority(cluster, gap_type)

        return GateImprovementIssue(
            symptom=symptom,
            root_cause_hypothesis=root_cause,
            gap_type=gap_type,
            gate_type=gate_type,
            gate_name=gate_name,
            trigger_strategy=trigger,
            command=command,
            risk_coverage=risk_coverage,
            acceptance=acceptance,
            priority=priority,
            evidence=evidence or [],
        )

    def _generate_symptom(self, cluster: FailureCluster) -> str:
        return (
            f"检测到重复失败模式：{cluster.signature} "
            f"(类型: {cluster.error_type})，近一段时间内出现 {cluster.count} 次"
        )

    def _generate_root_cause(self, cluster: FailureCluster, gap_type: GapType) -> str:
        if gap_type == GapType.MISSING_GATE:
            return (
                f"现有门禁体系缺少针对 {cluster.error_type} 类型错误的专门检查，"
                f"导致 {cluster.signature} 失败模式在执行过程中才被发现"
            )
        elif gap_type == GapType.COVERAGE_GAP:
            return (
                f"现有门禁对 {cluster.signature} 对应的场景覆盖不足，"
                f"同类问题反复出现，需要补充测试用例或扩大覆盖范围"
            )
        else:
            return (
                f"{cluster.signature} 相关门禁存在误报或偶发失败问题，"
                f"信噪比低，影响开发效率和门禁可信度"
            )

    def _determine_gate_type(self, cluster: FailureCluster) -> GateType:
        return self.ERROR_TYPE_TO_GATE_TYPE.get(
            cluster.error_type.lower(),
            GateType.UNIT,
        )

    def _generate_gate_name(self, cluster: FailureCluster, gap_type: GapType) -> str:
        prefix = {
            GapType.MISSING_GATE: "新增",
            GapType.COVERAGE_GAP: "增强",
            GapType.GATE_NOISE: "优化",
        }.get(gap_type, "")

        return f"{prefix} {cluster.error_type.capitalize()} - {cluster.signature[:30]}"

    def _determine_trigger(self, cluster: FailureCluster) -> GateTrigger:
        if cluster.error_type.lower() in ["mypy", "ruff", "lint", "typecheck"]:
            return GateTrigger.ON_PR
        if cluster.count >= 10:
            return GateTrigger.ON_PR
        return GateTrigger.NIGHTLY

    def _generate_command(self, cluster: FailureCluster, gate_type: GateType) -> str:
        if gate_type == GateType.STATIC:
            return f"cd <service> && {cluster.error_type} check ."
        elif gate_type == GateType.UNIT:
            return f"cd <service> && pytest -k '{cluster.signature[:20]}'"
        elif gate_type == GateType.CONTENT:
            return "python tools/content_check/<rule>.py --input <content_dir>"
        else:
            return f"bash tools/playtest/run_{cluster.signature[:20]}.sh"

    def _determine_risk_coverage(self, cluster: FailureCluster) -> List[str]:
        return self.ERROR_TYPE_TO_RISK_COVERAGE.get(
            cluster.error_type.lower(),
            ["regression"],
        )

    def _generate_acceptance(self, cluster: FailureCluster, gap_type: GapType) -> List[str]:
        acceptance = []

        if gap_type == GapType.MISSING_GATE:
            acceptance.append(
                f"新增门禁后，{cluster.signature} 类型错误应在 CI 阶段被拦截，"
                f"不应再以'执行中才发现'的方式出现"
            )
        elif gap_type == GapType.COVERAGE_GAP:
            acceptance.append(
                "补充测试用例后，同类失败复发率应下降 50% 以上"
            )
        else:
            acceptance.append(
                "优化后门禁误报率应低于 5%"
            )

        acceptance.append("30 天内同类失败次数 ≤ 2")
        acceptance.append("CI 耗时增加 ≤ 30 秒")

        return acceptance

    def _determine_priority(self, cluster: FailureCluster, gap_type: GapType) -> str:
        if gap_type == GapType.MISSING_GATE and cluster.count >= 10:
            return "p0"
        if cluster.count >= 5:
            return "p1"
        return "p2"

    def batch_generate(
        self,
        classified_gaps: List[Dict[str, Any]],
        clusters: Dict[str, FailureCluster],
        evidence: Optional[List[Dict[str, Any]]] = None,
    ) -> List[GateImprovementIssue]:
        issues = []
        for gap in classified_gaps:
            signature = gap["signature"]
            if signature in clusters:
                cluster = clusters[signature]
                gap_type = GapType(gap["gap_type"])
                issue = self.generate_issue(cluster, gap_type, evidence)
                issues.append(issue)
        return sorted(issues, key=lambda x: x.priority)