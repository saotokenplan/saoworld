"""WP3 审核效率派生指标（ops 看板三字段数据源）。

从 review-service 的 Prometheus 指标派生三项审核效率指标：
- auto_pass_rate: 自动审核通过率 = 自动审核通过数 / 自动审核总数
- manual_intervention_rate: 人工介入率 = 人工审核数 / 审核总数
- review_p95_minutes: 审核耗时 P95（分钟），由 review_duration_seconds Histogram 近似估算

派生口径与 `M4-审核效率看板指标定义.md` 第三节 K1/K2/K3 一致：
- K1 通过率 >70% 对应 auto_pass_rate
- K2 耗时 P95 <30min 对应 review_p95_minutes
- K3 人工介入率对应 manual_intervention_rate

相关指标定义见 `app/core/metrics.py`（M1/M2 埋点）：
- M2: reviews_total{result, review_type}
- M1: review_duration_seconds{review_type, object_type} Histogram
"""

from typing import Any

from prometheus_client import REGISTRY

_RESULTS = ("approved", "rejected", "manual_review")
_REVIEW_TYPES = ("auto", "manual")


def _read_reviews_total() -> dict[tuple[str, str], int]:
    """读取 reviews_total 各 (result, review_type) 当前累计值（来自 REGISTRY）。"""
    samples: dict[tuple[str, str], int] = {}
    for result in _RESULTS:
        for rtype in _REVIEW_TYPES:
            value = REGISTRY.get_sample_value(
                "reviews_total", {"result": result, "review_type": rtype}
            )
            if value is not None:
                samples[(result, rtype)] = int(value)
    return samples


def _read_duration_histogram() -> dict[str, Any]:
    """读取 review_duration_seconds Histogram 的桶累计与总量（跨标签聚合为全局直方图）。

    将带 (review_type, object_type) 标签的多个序列按桶边界累加，得到全局累计分布，
    用于整体 P95 估算。
    """
    name = "review_duration_seconds"
    buckets: list[float] = []
    cumulative: list[float] = []
    total_count = 0
    total_sum = 0.0

    for metric in REGISTRY.collect():
        for sample in metric.samples:
            if sample.name == f"{name}_bucket":
                le = float(sample.labels.get("le", "+Inf"))
                # +Inf 桶不参与线性插值，单独记录为总量
                if le == float("inf"):
                    continue
                # 跨序列按桶边界累加（假设所有序列桶边界一致）
                idx = _bucket_index(buckets, le)
                if idx is None:
                    buckets.append(le)
                    cumulative.append(sample.value)
                else:
                    cumulative[idx] += sample.value
            elif sample.name == f"{name}_count":
                total_count += int(sample.value)
            elif sample.name == f"{name}_sum":
                total_sum += float(sample.value)

    # 保证桶按升序排列（REGISTRY.collect 通常已有序，防御性排序）
    ordered = sorted(zip(buckets, cumulative), key=lambda pair: pair[0])
    buckets = [b for b, _ in ordered]
    cumulative = [c for _, c in ordered]
    return {"buckets": buckets, "cumulative": cumulative, "count": total_count, "sum": total_sum}


def _bucket_index(buckets: list[float], le: float) -> int | None:
    for i, existing in enumerate(buckets):
        if existing == le:
            return i
    return None


def histogram_quantile(q: float, buckets: list[float], cumulative: list[float]) -> float | None:
    """基于 Histogram 桶累计计数近似分位数（Prometheus 线性插值法）。

    Args:
        q: 分位（0~1），如 0.95 表示 P95
        buckets: 升序桶上界列表（秒）
        cumulative: 与 buckets 对应的累计计数（单调递增）

    Returns:
        分位值（秒）；样本数为 0 时返回 None。
    """
    if not buckets or not cumulative or cumulative[-1] == 0:
        return None

    rank = q * cumulative[-1]
    for i, upper in enumerate(buckets):
        lower = cumulative[i - 1] if i > 0 else 0.0
        bucket_count = cumulative[i] - lower
        if rank <= cumulative[i]:
            if bucket_count == 0:
                # 该桶无样本，继续向后找首个非空桶
                continue
            lower_bound = buckets[i - 1] if i > 0 else 0.0
            frac = (rank - lower) / bucket_count
            return lower_bound + frac * (upper - lower_bound)
    # 落入 +Inf 桶
    return buckets[-1]


def compute_review_efficiency(
    review_counts: dict[tuple[str, str], int],
    duration: dict[str, Any],
) -> dict[str, float | None]:
    """纯函数：由 (result, review_type) 计数与耗时 Histogram 派生三项指标。

    Args:
        review_counts: 映射 (result, review_type) -> 累计计数
        duration: {"buckets": [...], "cumulative": [...], "count": int, "sum": float}

    Returns:
        {
            "auto_pass_rate": float | None,
            "manual_intervention_rate": float | None,
            "review_p95_minutes": float | None,
        }
    """
    auto_total = sum(v for (_, rtype), v in review_counts.items() if rtype == "auto")
    manual_total = sum(v for (_, rtype), v in review_counts.items() if rtype == "manual")
    total = sum(review_counts.values())

    auto_approved = review_counts.get(("approved", "auto"), 0)
    auto_pass_rate = (auto_approved / auto_total) if auto_total > 0 else None

    manual_intervention_rate = (manual_total / total) if total > 0 else None

    p95_seconds = histogram_quantile(0.95, duration.get("buckets", []), duration.get("cumulative", []))
    review_p95_minutes = (p95_seconds / 60.0) if p95_seconds is not None else None

    return {
        "auto_pass_rate": auto_pass_rate,
        "manual_intervention_rate": manual_intervention_rate,
        "review_p95_minutes": review_p95_minutes,
    }


def collect_review_efficiency() -> dict[str, Any]:
    """读取 REGISTRY 当前指标并派生三项审核效率指标（运行时数据源）。"""
    review_counts = _read_reviews_total()
    duration = _read_duration_histogram()
    metrics = compute_review_efficiency(review_counts, duration)
    return {
        "auto_pass_rate": metrics["auto_pass_rate"],
        "manual_intervention_rate": metrics["manual_intervention_rate"],
        "review_p95_minutes": metrics["review_p95_minutes"],
        "raw": {
            "review_counts": {f"{r}:{t}": c for (r, t), c in review_counts.items()},
            "duration_count": duration["count"],
            "duration_sum": duration["sum"],
        },
    }
