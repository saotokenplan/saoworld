"""vote-service 业务指标定义。

使用 prometheus_client 定义业务指标，由 routes 层在关键操作发生时更新。
"""

from prometheus_client import Counter, Gauge, Histogram

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

# 投票资格拒绝次数（按玩家分组）
VOTE_ELIGIBILITY_REJECTED_TOTAL = Counter(
    "vote_eligibility_rejected_total",
    "因贡献度不足被拒绝的投票次数",
    labelnames=["player_id"],
)

# 讨论发布总数
VOTE_DISCUSSION_CREATED_TOTAL = Counter(
    "vote_discussion_created_total",
    "讨论发布总数",
)

# 讨论点赞总数
VOTE_DISCUSSION_LIKED_TOTAL = Counter(
    "vote_discussion_liked_total",
    "讨论点赞总数",
)

# 回复发布总数
VOTE_REPLY_CREATED_TOTAL = Counter(
    "vote_reply_created_total",
    "回复发布总数",
)

# 回复点赞总数
VOTE_REPLY_LIKED_TOTAL = Counter(
    "vote_reply_liked_total",
    "回复点赞总数",
)


def record_vote_submission() -> None:
    """记录一次成功的投票提交。"""
    VOTE_SUBMISSIONS_TOTAL.inc()


def record_vote_cycle_transition(from_status: str, to_status: str) -> None:
    """记录一次投票周期状态迁移。"""
    VOTE_CYCLE_TRANSITIONS_TOTAL.labels(from_status=from_status, to_status=to_status).inc()


def record_vote_eligibility_rejected(player_id: str) -> None:
    """记录一次因贡献度不足被拒绝的投票。"""
    VOTE_ELIGIBILITY_REJECTED_TOTAL.labels(player_id=player_id).inc()


def record_discussion_created() -> None:
    """记录一次讨论发布。"""
    VOTE_DISCUSSION_CREATED_TOTAL.inc()


def record_discussion_liked() -> None:
    """记录一次讨论点赞。"""
    VOTE_DISCUSSION_LIKED_TOTAL.inc()


def record_reply_created() -> None:
    """记录一次回复发布。"""
    VOTE_REPLY_CREATED_TOTAL.inc()


def record_reply_liked() -> None:
    """记录一次回复点赞。"""
    VOTE_REPLY_LIKED_TOTAL.inc()


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


VOTE_PROGRESS_QUERIES_TOTAL = Counter(
    "vote_progress_queries_total",
    "投票进度查询总数",
)


def record_vote_progress_query() -> None:
    """记录一次投票进度查询。"""
    VOTE_PROGRESS_QUERIES_TOTAL.inc()


VOTE_ANOMALIES_DETECTED_TOTAL = Counter(
    "vote_anomalies_detected_total",
    "检测到的投票异常总数",
    labelnames=["anomaly_type", "severity"],
)

VOTE_ANOMALIES_RESOLVED_TOTAL = Counter(
    "vote_anomalies_resolved_total",
    "已解决的投票异常总数",
    labelnames=["resolution_type"],
)

VOTE_ANOMALY_DETECTION_DURATION = Histogram(
    "vote_anomaly_detection_duration_seconds",
    "投票异常检测耗时",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)


def record_anomaly_detected(anomaly_type: str, severity: str) -> None:
    """记录一次检测到的投票异常。"""
    VOTE_ANOMALIES_DETECTED_TOTAL.labels(
        anomaly_type=anomaly_type, severity=severity
    ).inc()


def record_anomaly_resolved(resolution_type: str) -> None:
    """记录一次已解决的投票异常。"""
    VOTE_ANOMALIES_RESOLVED_TOTAL.labels(resolution_type=resolution_type).inc()


def observe_anomaly_detection_duration(duration: float) -> None:
    """记录异常检测耗时。"""
    VOTE_ANOMALY_DETECTION_DURATION.observe(duration)
