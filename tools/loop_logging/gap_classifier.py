from __future__ import annotations

from typing import List, Dict, Any

from .schema import GapType
from .clusterer import FailureCluster


class GapClassifier:
    @classmethod
    def classify_gap(
        cls,
        cluster: FailureCluster,
        existing_gate_ids: List[str],
    ) -> Dict[str, Any]:
        gap_type = cls._determine_gap_type(cluster, existing_gate_ids)
        confidence = cls._calculate_confidence(cluster, gap_type)
        suggested_action = cls._suggest_action(cluster, gap_type)

        return {
            "signature": cluster.signature,
            "error_type": cluster.error_type,
            "gap_type": gap_type.value,
            "confidence": confidence,
            "suggested_action": suggested_action,
            "cluster_count": cluster.count,
            "gate_names": sorted(list(cluster.gate_names)),
            "examples": cluster.examples[:3],
        }

    @classmethod
    def _determine_gap_type(
        cls,
        cluster: FailureCluster,
        existing_gate_ids: List[str],
    ) -> GapType:
        error_type = cluster.error_type.lower()

        if error_type in ["mypy", "ruff", "lint", "typecheck"]:
            if cls._is_gate_coverage_gap(cluster, existing_gate_ids):
                return GapType.COVERAGE_GAP
            return GapType.MISSING_GATE

        if error_type in ["pytest", "test", "assertion"]:
            if cls._is_repeated_test_failure(cluster):
                return GapType.COVERAGE_GAP
            if cls._is_test_flakiness(cluster):
                return GapType.GATE_NOISE
            return GapType.COVERAGE_GAP

        if error_type in ["attr-error", "type-error", "value-error", "key-error", "index-error"]:
            return GapType.COVERAGE_GAP

        if error_type in ["timeout-error", "conn-error", "runtime-error"]:
            if cls._is_environmental(cluster):
                return GapType.GATE_NOISE
            return GapType.COVERAGE_GAP

        if error_type in ["world-rule", "reward-budget", "safety-rule", "duplication-rule"]:
            return GapType.COVERAGE_GAP

        if cluster.count > 10:
            return GapType.MISSING_GATE

        return GapType.COVERAGE_GAP

    @classmethod
    def _is_gate_coverage_gap(
        cls,
        cluster: FailureCluster,
        existing_gate_ids: List[str],
    ) -> bool:
        for gate_id in cluster.gate_ids:
            if gate_id in existing_gate_ids:
                return True
        return False

    @classmethod
    def _is_repeated_test_failure(cls, cluster: FailureCluster) -> bool:
        return cluster.count >= 5

    @classmethod
    def _is_test_flakiness(cls, cluster: FailureCluster) -> bool:
        if "flaky" in cluster.signature.lower():
            return True
        if cluster.count >= 3 and any("flaky" in ex.lower() for ex in cluster.examples):
            return True
        return False

    @classmethod
    def _is_environmental(cls, cluster: FailureCluster) -> bool:
        keywords = ["timeout", "connection", "network", "database", "redis"]
        for keyword in keywords:
            if keyword in cluster.signature.lower():
                return True
            for example in cluster.examples:
                if keyword in example.lower():
                    return True
        return False

    @classmethod
    def _calculate_confidence(
        cls,
        cluster: FailureCluster,
        gap_type: GapType,
    ) -> float:
        base_confidence = 0.5

        if cluster.count >= 10:
            base_confidence += 0.3
        elif cluster.count >= 5:
            base_confidence += 0.15

        if len(cluster.examples) >= 3:
            base_confidence += 0.1

        if gap_type == GapType.COVERAGE_GAP and cls._is_repeated_test_failure(cluster):
            base_confidence += 0.1

        if gap_type == GapType.GATE_NOISE and cls._is_test_flakiness(cluster):
            base_confidence += 0.15

        return min(1.0, base_confidence)

    @classmethod
    def _suggest_action(
        cls,
        cluster: FailureCluster,
        gap_type: GapType,
    ) -> str:
        if gap_type == GapType.MISSING_GATE:
            return f"新增门禁：针对 {cluster.error_type} 类型的 {cluster.signature} 错误添加专门的静态检查或单元测试"

        if gap_type == GapType.COVERAGE_GAP:
            return f"增强覆盖：为 {cluster.signature} 对应的失败模式补充测试用例或扩大现有门禁的覆盖范围"

        if gap_type == GapType.GATE_NOISE:
            return f"降低噪音：调整 {cluster.signature} 相关门禁的阈值或添加白名单，减少误报"

        return f"处理 {cluster.signature} 失败模式"

    @classmethod
    def batch_classify(
        cls,
        clusters: List[FailureCluster],
        existing_gate_ids: List[str],
    ) -> List[Dict[str, Any]]:
        results = []
        for cluster in clusters:
            result = cls.classify_gap(cluster, existing_gate_ids)
            if result["confidence"] >= 0.6:
                results.append(result)
        return sorted(results, key=lambda x: x["confidence"], reverse=True)
