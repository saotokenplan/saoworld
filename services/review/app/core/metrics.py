"""review-service 业务指标定义。

使用 prometheus_client 定义业务指标，由 routes 层在关键操作发生时更新。
"""

from prometheus_client import Counter, Gauge

# 审核数（按结果分组：approved/rejected/manual_review）
REVIEWS_TOTAL = Counter(
    "reviews_total",
    "审核数（按结果）",
    labelnames=["result"],
)

# 审核操作数（按动作分组：create/approve/reject）
REVIEW_OPERATIONS_TOTAL = Counter(
    "review_operations_total",
    "审核操作数（按动作）",
    labelnames=["action"],
)

# 当前审核数（按风险等级分组的 Gauge）
REVIEWS_BY_RISK_LEVEL = Gauge(
    "reviews_by_risk_level",
    "审核数（按风险等级）",
    labelnames=["risk_level"],
)


def record_review_create() -> None:
    """记录一次审核创建。"""
    REVIEW_OPERATIONS_TOTAL.labels(action="create").inc()


def record_review_result(result: str) -> None:
    """记录一次审核结果（approved/rejected/manual_review）。"""
    REVIEWS_TOTAL.labels(result=result).inc()


def set_reviews_by_risk_level(risk_counts: dict[str, int]) -> None:
    """设置按风险等级分组的当前审核数。

    Args:
        risk_counts: 风险等级到数量的映射，例如 {"low": 1, "medium": 2}
    """
    for risk_label in ("low", "medium", "high", "critical"):
        REVIEWS_BY_RISK_LEVEL.labels(risk_level=risk_label).set(
            risk_counts.get(risk_label, 0)
        )
