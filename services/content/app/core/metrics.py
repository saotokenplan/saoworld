"""content-service 业务指标定义。"""

from prometheus_client import Counter, Gauge

# 内容包操作次数（按动作类型分组：create、release、rollback）
CONTENT_PACKAGE_OPERATIONS_TOTAL = Counter(
    "content_package_operations_total",
    "内容包操作次数（按动作类型）",
    labelnames=["action"],
)

# 内容包发布次数（按模式分组：gray、full）
CONTENT_RELEASES_TOTAL = Counter(
    "content_releases_total",
    "内容包发布次数（按模式）",
    labelnames=["mode"],
)

# 内容包回滚次数
CONTENT_ROLLBACKS_TOTAL = Counter(
    "content_rollbacks_total",
    "内容包回滚次数",
)

# 当前内容包数（按状态分组的 Gauge）
CONTENT_PACKAGES_BY_STATUS = Gauge(
    "content_packages_by_status",
    "内容包数（按状态）",
    labelnames=["status"],
)


def record_package_create() -> None:
    """记录一次内容包创建。"""
    CONTENT_PACKAGE_OPERATIONS_TOTAL.labels(action="create").inc()


def record_package_release(mode: str) -> None:
    """记录一次内容包发布。

    Args:
        mode: 发布模式（gray、full）
    """
    CONTENT_RELEASES_TOTAL.labels(mode=mode).inc()
    CONTENT_PACKAGE_OPERATIONS_TOTAL.labels(action="release").inc()


def record_package_rollback() -> None:
    """记录一次内容包回滚。"""
    CONTENT_ROLLBACKS_TOTAL.inc()
    CONTENT_PACKAGE_OPERATIONS_TOTAL.labels(action="rollback").inc()


def set_packages_by_status(status_counts: dict[str, int]) -> None:
    """设置按状态分组的内容包数。"""
    for status_label in ("packaged", "gray", "live", "archived", "rolled_back"):
        CONTENT_PACKAGES_BY_STATUS.labels(status=status_label).set(
            status_counts.get(status_label, 0)
        )
