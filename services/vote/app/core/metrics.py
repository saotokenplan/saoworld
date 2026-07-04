"""vote-service 业务指标定义。

使用 prometheus_client 定义业务指标，由 routes 层在关键操作发生时更新。
"""

from prometheus_client import Counter, Gauge

# 投票提交总数（成功提交后递增）
VOTE_SUBMISSIONS_TOTAL = Counter(
    "vote_submissions_total",
    "投票提交总数",
)

# 投票周期数（按状态分组的当前值）
VOTE_CYCLES_BY_STATUS = Gauge(
    "vote_cycles_by_status",
    "投票周期数（按状态）",
    labelnames=["status"],
)

# 候选项数（按状态分组的当前值）
VOTE_CANDIDATES_BY_STATUS = Gauge(
    "vote_candidates_by_status",
    "候选项数（按状态）",
    labelnames=["status"],
)

# 投票周期状态迁移次数（按 from_status/to_status 分组）
VOTE_CYCLE_TRANSITIONS_TOTAL = Counter(
    "vote_cycle_transitions_total",
    "投票周期状态迁移次数",
    labelnames=["from_status", "to_status"],
)


def record_vote_submission() -> None:
    """记录一次成功的投票提交。"""
    VOTE_SUBMISSIONS_TOTAL.inc()


def record_vote_cycle_transition(from_status: str, to_status: str) -> None:
    """记录一次投票周期状态迁移。"""
    VOTE_CYCLE_TRANSITIONS_TOTAL.labels(from_status=from_status, to_status=to_status).inc()


def set_vote_cycles_by_status(status_counts: dict[str, int]) -> None:
    """设置按状态分组的投票周期数。

    Args:
        status_counts: 状态到数量的映射，例如 {"draft": 1, "open": 2}
    """
    # 先清零所有已知状态，避免残留
    for status_label in ("draft", "scheduled", "open", "closed", "finalized"):
        VOTE_CYCLES_BY_STATUS.labels(status=status_label).set(status_counts.get(status_label, 0))


def set_vote_candidates_by_status(status_counts: dict[str, int]) -> None:
    """设置按状态分组的候选项数。"""
    for status_label in ("active", "withdrawn", "selected"):
        VOTE_CANDIDATES_BY_STATUS.labels(status=status_label).set(
            status_counts.get(status_label, 0)
        )
