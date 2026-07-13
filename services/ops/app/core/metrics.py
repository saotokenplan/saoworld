"""ops-service 业务指标定义。

使用 prometheus_client 定义业务指标，由 routes 层在关键操作发生时更新。
"""

from prometheus_client import Counter, Gauge

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


# 运营事件指标
OPS_EVENTS_CREATED_TOTAL = Counter(
    "ops_events_created_total",
    "运营事件创建数",
    labelnames=["event_type"],
)

OPS_EVENTS_ACTIVE_COUNT = Gauge(
    "ops_events_active_count",
    "当前生效的运营事件数",
)

OPS_EVENT_TRIGGERS_TOTAL = Counter(
    "ops_event_triggers_total",
    "运营事件触发次数",
    labelnames=["event_type"],
)


def record_event_created(event_type: str) -> None:
    """记录一次事件创建。"""
    OPS_EVENTS_CREATED_TOTAL.labels(event_type=event_type).inc()


def record_event_trigger(event_type: str) -> None:
    """记录一次事件触发。"""
    OPS_EVENT_TRIGGERS_TOTAL.labels(event_type=event_type).inc()


def set_active_events_count(count: int) -> None:
    """设置当前生效事件数。"""
    OPS_EVENTS_ACTIVE_COUNT.set(count)
