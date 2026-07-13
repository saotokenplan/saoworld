"""ops-service 业务指标定义。

使用 prometheus_client 定义业务指标，由 routes 层在关键操作发生时更新。
"""

from prometheus_client import Counter

# 运营操作数（按动作类型分组：dashboard_view、action_query、system_status）
OPS_ACTIONS_TOTAL = Counter(
    "ops_actions_total",
    "运营操作数（按动作类型）",
    labelnames=["action_type"],
)

# 仪表盘访问数
OPS_DASHBOARD_VIEWS_TOTAL = Counter(
    "ops_dashboard_views_total",
    "仪表盘访问数",
)


def record_dashboard_view() -> None:
    """记录一次仪表盘访问。"""
    OPS_DASHBOARD_VIEWS_TOTAL.inc()


def record_ops_action(action_type: str) -> None:
    """记录一次运营操作。

    Args:
        action_type: 动作类型，如 action_query、system_status
    """
    OPS_ACTIONS_TOTAL.labels(action_type=action_type).inc()


# 投票周期操作数（按操作类型分组：create、schedule、open、close、finalize、list、detail）
OPS_VOTE_CYCLE_OPS_TOTAL = Counter(
    "ops_vote_cycle_ops_total",
    "投票周期操作数（按操作类型）",
    labelnames=["operation"],
)

# 内容包操作数（按操作类型分组：release、rollback、list、detail）
OPS_CONTENT_OPS_TOTAL = Counter(
    "ops_content_ops_total",
    "内容包操作数（按操作类型）",
    labelnames=["operation"],
)

# 审核操作数（按操作类型分组：approve、reject、list、stats）
OPS_REVIEW_OPS_TOTAL = Counter(
    "ops_review_ops_total",
    "审核操作数（按操作类型）",
    labelnames=["operation"],
)


def record_vote_cycle_op(operation: str) -> None:
    """记录一次投票周期操作。"""
    OPS_VOTE_CYCLE_OPS_TOTAL.labels(operation=operation).inc()


def record_content_op(operation: str) -> None:
    """记录一次内容包操作。"""
    OPS_CONTENT_OPS_TOTAL.labels(operation=operation).inc()


def record_review_op(operation: str) -> None:
    """记录一次审核操作。"""
    OPS_REVIEW_OPS_TOTAL.labels(operation=operation).inc()
