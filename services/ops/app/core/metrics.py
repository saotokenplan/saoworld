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
