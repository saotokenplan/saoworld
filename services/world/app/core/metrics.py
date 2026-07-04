"""world-service 业务指标定义。"""

from prometheus_client import Counter, Gauge

# 区域操作次数（按动作类型分组：create、status_update）
WORLD_REGION_OPERATIONS_TOTAL = Counter(
    "world_region_operations_total",
    "区域操作次数（按动作类型）",
    labelnames=["action"],
)

# 区域状态迁移次数（按 from_status/to_status 分组）
WORLD_REGION_TRANSITIONS_TOTAL = Counter(
    "world_region_transitions_total",
    "区域状态迁移次数",
    labelnames=["from_status", "to_status"],
)

# 当前区域数（按状态分组的 Gauge）
WORLD_REGIONS_BY_STATUS = Gauge(
    "world_regions_by_status",
    "区域数（按状态）",
    labelnames=["status"],
)


def record_region_create() -> None:
    """记录一次区域创建。"""
    WORLD_REGION_OPERATIONS_TOTAL.labels(action="create").inc()


def record_region_status_transition(from_status: str, to_status: str) -> None:
    """记录一次区域状态迁移。"""
    WORLD_REGION_TRANSITIONS_TOTAL.labels(from_status=from_status, to_status=to_status).inc()
    WORLD_REGION_OPERATIONS_TOTAL.labels(action="status_update").inc()


def set_regions_by_status(status_counts: dict[str, int]) -> None:
    """设置按状态分组的区域数。"""
    for status_label in ("locked", "active", "unstable", "archived"):
        WORLD_REGIONS_BY_STATUS.labels(status=status_label).set(
            status_counts.get(status_label, 0)
        )
