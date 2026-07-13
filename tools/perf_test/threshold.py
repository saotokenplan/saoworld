"""阈值校验模块。

将 LatencyStats 与一组阈值（p95/p99/error_rate 等）对比，输出校验结果。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .stats import LatencyStats


@dataclass
class Threshold:
    """单个阈值定义。"""

    name: str
    metric: str  # p50_ms / p95_ms / p99_ms / avg_ms / max_ms / error_rate
    max_value: float
    severity: str = "blocker"  # blocker | warn


@dataclass
class ThresholdResult:
    """单个阈值的校验结果。"""

    name: str
    metric: str
    threshold: float
    actual: float
    severity: str
    passed: bool

    def to_dict(self) -> dict[str, str | float | bool]:
        """转换为字典格式。"""
        return {
            "name": self.name,
            "metric": self.metric,
            "threshold": self.threshold,
            "actual": self.actual,
            "severity": self.severity,
            "passed": self.passed,
        }


@dataclass
class ThresholdCheckSummary:
    """所有阈值校验的汇总结果。"""

    results: list[ThresholdResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """所有 blocker 级别都通过。"""
        return all(r.passed or r.severity == "warn" for r in self.results)

    @property
    def blocker_failed(self) -> list[ThresholdResult]:
        """所有 blocker 级别失败的项。"""
        return [r for r in self.results if not r.passed and r.severity == "blocker"]

    def to_dict(self) -> dict[str, object]:
        """转换为字典格式。"""
        return {
            "passed": self.passed,
            "blocker_failed": [r.to_dict() for r in self.blocker_failed],
            "results": [r.to_dict() for r in self.results],
        }


_METRIC_KEYS = {
    "p50_ms",
    "p95_ms",
    "p99_ms",
    "avg_ms",
    "max_ms",
    "min_ms",
    "qps",
    "error_rate",
}


def check_thresholds(
    stats: LatencyStats,
    thresholds: list[Threshold],
) -> ThresholdCheckSummary:
    """检查 LatencyStats 是否通过所有阈值。

    Args:
        stats: 延迟统计结果
        thresholds: 阈值定义列表

    Returns:
        校验汇总
    """
    summary = ThresholdCheckSummary()
    for th in thresholds:
        if th.metric not in _METRIC_KEYS:
            result = ThresholdResult(
                name=th.name,
                metric=th.metric,
                threshold=th.max_value,
                actual=float("nan"),
                severity=th.severity,
                passed=False,
            )
        else:
            actual = float(getattr(stats, th.metric))
            result = ThresholdResult(
                name=th.name,
                metric=th.metric,
                threshold=th.max_value,
                actual=actual,
                severity=th.severity,
                passed=actual <= th.max_value,
            )
        summary.results.append(result)
    return summary


# 项目默认阈值（参考 docs/20-specs/backend-data-spec.md、docs/packages/first-slice/acceptance/）
DEFAULT_THRESHOLDS: dict[str, list[Threshold]] = {
    "vote_submit": [
        Threshold(name="vote_submit_p95", metric="p95_ms", max_value=300.0, severity="blocker"),
        Threshold(name="vote_submit_p99", metric="p99_ms", max_value=500.0, severity="warn"),
        Threshold(name="vote_submit_error_rate", metric="error_rate", max_value=0.01, severity="blocker"),
    ],
    "vote_query": [
        Threshold(name="vote_query_p95", metric="p95_ms", max_value=100.0, severity="blocker"),
        Threshold(name="vote_query_p99", metric="p99_ms", max_value=200.0, severity="warn"),
        Threshold(name="vote_query_error_rate", metric="error_rate", max_value=0.01, severity="blocker"),
    ],
    "content_query": [
        Threshold(name="content_query_p95", metric="p95_ms", max_value=100.0, severity="blocker"),
        Threshold(name="content_query_p99", metric="p99_ms", max_value=200.0, severity="warn"),
        Threshold(name="content_query_error_rate", metric="error_rate", max_value=0.01, severity="blocker"),
    ],
}


def get_default_thresholds(scenario_name: str) -> list[Threshold]:
    """根据场景名获取默认阈值列表。

    Args:
        scenario_name: 场景名

    Returns:
        阈值列表（若未找到则返回空列表）
    """
    return list(DEFAULT_THRESHOLDS.get(scenario_name, []))
