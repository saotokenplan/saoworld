"""review-service 业务指标定义。

使用 prometheus_client 定义业务指标，由 routes 层在关键操作发生时更新。

WP3（M4-审核效率看板指标定义.md）实施期埋点：
- M2: `reviews_total` 增加 `review_type` 标签，区分自动/人工终局判定
- M1: 新增 `review_duration_seconds` 耗时 Histogram（K2 在线数据源）
- M4: 新增 `review_rule_decisions_total` 规则归因 Counter（A3 归因面板）
"""

from prometheus_client import Counter, Gauge, Histogram

# 审核数（按结果分组：approved/rejected/manual_review；按 review_type 区分自动/人工）
# M2: 增加 review_type 标签，修复 auto 路径仅 is_automatic 时计数的口径失真
REVIEWS_TOTAL = Counter(
    "reviews_total",
    "审核数（按结果与审核类型）",
    labelnames=["result", "review_type"],
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

# M1: 审核耗时 Histogram（K2 在线数据源，依赖运行时真实流量）
# 标签 review_type 区分 auto/manual，object_type 用于分层（与 K2 口径一致）
REVIEW_DURATION_SECONDS = Histogram(
    "review_duration_seconds",
    "审核耗时（秒）：审核记录创建到终结的时长",
    labelnames=["review_type", "object_type"],
    buckets=[1.0, 5.0, 15.0, 60.0, 300.0, 900.0, 1800.0, 3600.0],
)

# M4: 规则归因 Counter（A3 规则判定分布，用于调优归因面板）
REVIEW_RULE_DECISIONS_TOTAL = Counter(
    "review_rule_decisions_total",
    "自动审核引擎各规则判定分布",
    labelnames=["rule", "result"],
)


def record_review_create() -> None:
    """记录一次审核创建。"""
    REVIEW_OPERATIONS_TOTAL.labels(action="create").inc()


def record_review_result(result: str, review_type: str) -> None:
    """记录一次审核终局结果（approved/rejected/manual_review）。

    M2: 新增 review_type 标签（"auto" 自动审核 / "manual" 人工审核），
    由调用方按实际审核类型传入；auto 路径对所有终局判定统一计数。
    """
    REVIEWS_TOTAL.labels(result=result, review_type=review_type).inc()


def record_review_duration(review_type: str, object_type: str, seconds: float) -> None:
    """记录一次审核耗时（秒）。

    M1: K2 在线数据源。seconds 为审核记录 created_at -> updated_at 的时长。
    """
    REVIEW_DURATION_SECONDS.labels(review_type=review_type, object_type=object_type).observe(seconds)


def record_rule_decision(rule: str, result: str) -> None:
    """记录一条自动审核规则的判定结果。

    M4: result 为规则判定（approved/rejected/manual_review），规则不适用时记 "not_applied"，
    规则抛异常时记 "error"，均用于 A3 规则归因面板。
    """
    REVIEW_RULE_DECISIONS_TOTAL.labels(rule=rule, result=result).inc()


def set_reviews_by_risk_level(risk_counts: dict[str, int]) -> None:
    """设置按风险等级分组的当前审核数。

    Args:
        risk_counts: 风险等级到数量的映射，例如 {"low": 1, "medium": 2}
    """
    for risk_label in ("low", "medium", "high", "critical"):
        REVIEWS_BY_RISK_LEVEL.labels(risk_level=risk_label).set(
            risk_counts.get(risk_label, 0)
        )
