"""generation-service 业务指标定义。

使用 prometheus_client 定义业务指标，由 routes 层在关键操作发生时更新。
"""

from prometheus_client import Counter, Gauge

# 生成请求数（按状态分组：pending/processing/succeeded/failed_retryable/failed_permanent）
GENERATION_REQUESTS_TOTAL = Counter(
    "generation_requests_total",
    "生成请求数（按状态）",
    labelnames=["status"],
)

# 生成对象数（按状态分组：pending_review/approved/rejected/needs_revision）
GENERATED_OBJECTS_TOTAL = Counter(
    "generated_objects_total",
    "生成对象数（按状态）",
    labelnames=["status"],
)

# 当前生成请求数（按状态分组的 Gauge）
GENERATION_REQUESTS_BY_STATUS = Gauge(
    "generation_requests_by_status",
    "当前生成请求数（按状态）",
    labelnames=["status"],
)


def record_generation_request_status(status: str) -> None:
    """记录一次生成请求状态变更。"""
    GENERATION_REQUESTS_TOTAL.labels(status=status).inc()


def record_generated_object_status(status: str) -> None:
    """记录一次生成对象状态变更。"""
    GENERATED_OBJECTS_TOTAL.labels(status=status).inc()


def set_generation_requests_by_status(status_counts: dict[str, int]) -> None:
    """设置按状态分组的当前生成请求数。

    Args:
        status_counts: 状态到数量的映射，例如 {"pending": 1, "processing": 2}
    """
    for status_label in (
        "pending",
        "processing",
        "succeeded",
        "failed_retryable",
        "failed_permanent",
    ):
        GENERATION_REQUESTS_BY_STATUS.labels(status=status_label).set(
            status_counts.get(status_label, 0)
        )
