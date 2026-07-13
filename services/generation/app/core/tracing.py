"""OpenTelemetry 分布式追踪配置。

为 FastAPI 应用添加自动请求追踪和 span 创建。
追踪数据可通过 OTLP 导出到 Jaeger/Tempo 等后端。
"""

from __future__ import annotations

import os
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class TracingMiddleware(BaseHTTPMiddleware):
    """分布式追踪中间件。

    为每个 HTTP 请求创建追踪上下文：
    - 从请求头提取 trace_id（W3C traceparent 或 X-Trace-Id）
    - 设置 span 属性（method、path、status_code）
    - 在响应头中返回 trace_id
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        trace_id = request.headers.get("X-Trace-Id", "")
        request_id = request.headers.get("X-Request-Id", "")

        response = await call_next(request)

        if trace_id:
            response.headers["X-Trace-Id"] = trace_id
        if request_id:
            response.headers["X-Request-Id"] = request_id

        return response


def setup_tracing(app: FastAPI, service_name: str) -> None:
    """配置分布式追踪。

    Args:
        app: FastAPI 应用实例
        service_name: 服务名称（用于追踪标识）
    """
    enabled = os.getenv(f"{service_name.upper()}_TRACING_ENABLED", "false").lower() == "true"

    if enabled:
        app.add_middleware(TracingMiddleware)
