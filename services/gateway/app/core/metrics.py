"""gateway-service 业务指标定义。"""

from prometheus_client import Counter

# 代理请求数（按目标服务分组）
GATEWAY_PROXY_REQUESTS_TOTAL = Counter(
    "gateway_proxy_requests_total",
    "代理请求数（按目标服务）",
    labelnames=["service"],
)

# 限流触发次数
GATEWAY_RATE_LIMIT_HITS_TOTAL = Counter(
    "gateway_rate_limit_hits_total",
    "限流触发次数",
)

# 认证失败次数
GATEWAY_AUTH_FAILURES_TOTAL = Counter(
    "gateway_auth_failures_total",
    "认证失败次数",
)


def record_proxy_request(service: str) -> None:
    """记录一次代理请求。

    Args:
        service: 目标服务名（vote-service、world-service 等）
    """
    GATEWAY_PROXY_REQUESTS_TOTAL.labels(service=service).inc()


def record_rate_limit_hit() -> None:
    """记录一次限流触发。"""
    GATEWAY_RATE_LIMIT_HITS_TOTAL.inc()


def record_auth_failure() -> None:
    """记录一次认证失败。"""
    GATEWAY_AUTH_FAILURES_TOTAL.inc()
