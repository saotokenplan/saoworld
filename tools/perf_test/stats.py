"""延迟统计计算模块。

输入一系列响应耗时（毫秒），输出：
- count（请求总数）
- min / max / avg（毫秒）
- p50 / p95 / p99（毫秒）
- qps（每秒请求数，依赖 duration_seconds）
- error_count / error_rate

使用线性插值计算百分位数（与 numpy.percentile 行为一致），无外部依赖。
"""

from __future__ import annotations

import math
import statistics
from dataclasses import asdict, dataclass
from typing import Sequence


@dataclass
class LatencyStats:
    """延迟统计结果。"""

    count: int = 0
    error_count: int = 0
    min_ms: float = 0.0
    max_ms: float = 0.0
    avg_ms: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    qps: float = 0.0
    duration_seconds: float = 0.0
    error_rate: float = 0.0

    def to_dict(self) -> dict[str, float | int]:
        """转换为字典格式。"""
        return asdict(self)


def _percentile(sorted_values: Sequence[float], p: float) -> float:
    """计算百分位数（线性插值，与 numpy.percentile 行为一致）。

    Args:
        sorted_values: 已排序的值序列
        p: 百分位（0-100）

    Returns:
        对应百分位的值
    """
    if not sorted_values:
        return 0.0
    if p <= 0:
        return float(sorted_values[0])
    if p >= 100:
        return float(sorted_values[-1])

    n = len(sorted_values)
    # 线性插值，rank 范围 [0, n-1]
    rank = (p / 100.0) * (n - 1)
    lower = int(math.floor(rank))
    upper = int(math.ceil(rank))
    if lower == upper:
        return float(sorted_values[lower])
    weight = rank - lower
    return float(sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight)


def compute_stats(
    latencies_ms: Sequence[float],
    error_count: int = 0,
    duration_seconds: float = 0.0,
) -> LatencyStats:
    """计算延迟统计指标。

    Args:
        latencies_ms: 所有成功请求的响应耗时列表（毫秒）
        error_count: 失败请求数量
        duration_seconds: 压测总耗时（秒）

    Returns:
        LatencyStats 对象
    """
    count = len(latencies_ms) + error_count
    if count == 0:
        return LatencyStats()

    error_rate = error_count / count if count > 0 else 0.0
    qps = count / duration_seconds if duration_seconds > 0 else 0.0

    if not latencies_ms:
        # 全部失败
        return LatencyStats(
            count=count,
            error_count=error_count,
            min_ms=0.0,
            max_ms=0.0,
            avg_ms=0.0,
            p50_ms=0.0,
            p95_ms=0.0,
            p99_ms=0.0,
            qps=qps,
            duration_seconds=duration_seconds,
            error_rate=error_rate,
        )

    sorted_vals = sorted(float(v) for v in latencies_ms)
    return LatencyStats(
        count=count,
        error_count=error_count,
        min_ms=sorted_vals[0],
        max_ms=sorted_vals[-1],
        avg_ms=statistics.fmean(sorted_vals),
        p50_ms=_percentile(sorted_vals, 50),
        p95_ms=_percentile(sorted_vals, 95),
        p99_ms=_percentile(sorted_vals, 99),
        qps=qps,
        duration_seconds=duration_seconds,
        error_rate=error_rate,
    )
