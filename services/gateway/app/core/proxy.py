from typing import Optional

import httpx
import structlog
from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.core.metrics import record_proxy_request

logger = structlog.get_logger()

ROUTE_MAP = {
    "/api/v1/votes": settings.vote_service_url,
    "/api/v1/world": settings.world_service_url,
    "/api/v1/content": settings.content_service_url,
    "/api/v1/generation": settings.generation_service_url,
    "/api/v1/review": settings.review_service_url,
}

SERVICE_NAME_MAP = {
    "/api/v1/votes": "vote-service",
    "/api/v1/world": "world-service",
    "/api/v1/content": "content-service",
    "/api/v1/generation": "generation-service",
    "/api/v1/review": "review-service",
}


async def get_service_url(path: str) -> Optional[str]:
    for prefix, url in ROUTE_MAP.items():
        if path.startswith(prefix):
            return url
    return None


async def get_service_name(path: str) -> Optional[str]:
    for prefix, name in SERVICE_NAME_MAP.items():
        if path.startswith(prefix):
            return name
    return None


async def proxy_request(request: Request) -> StreamingResponse:
    service_url = await get_service_url(request.url.path)
    if not service_url:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "未找到对应的服务"},
        )

    # 业务指标：代理请求计数
    service_name = await get_service_name(request.url.path) or "unknown"
    record_proxy_request(service_name)

    request_id = request.headers.get(settings.request_id_header)
    trace_id = request.headers.get(settings.trace_id_header)

    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}

    if request_id:
        headers[settings.request_id_header] = request_id
    if trace_id:
        headers[settings.trace_id_header] = trace_id

    proxy_url = f"{service_url}{request.url.path}"
    if request.url.query:
        proxy_url += f"?{request.url.query}"

    logger.info(
        "proxy_request",
        method=request.method,
        path=request.url.path,
        target_url=proxy_url,
        request_id=request_id,
        trace_id=trace_id,
    )

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            body = await request.body()
            response = await client.request(
                method=request.method,
                url=proxy_url,
                headers=headers,
                content=body,
                follow_redirects=False,
            )

            response_headers = {k: v for k, v in response.headers.items()}
            if request_id:
                response_headers[settings.request_id_header] = request_id
            if trace_id:
                response_headers[settings.trace_id_header] = trace_id

            return StreamingResponse(
                content=response.aiter_raw(),
                status_code=response.status_code,
                headers=response_headers,
            )
    except httpx.ConnectError:
        logger.error("proxy_connection_failed", target_url=proxy_url)
        raise HTTPException(
            status_code=503,
            detail={"code": "SERVICE_UNAVAILABLE", "message": "后端服务不可用"},
        )
    except httpx.TimeoutException:
        logger.error("proxy_timeout", target_url=proxy_url)
        raise HTTPException(
            status_code=504,
            detail={"code": "GATEWAY_TIMEOUT", "message": "请求超时"},
        )
    except Exception as exc:
        logger.exception("proxy_request_failed", error=str(exc), target_url=proxy_url)
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": "网关内部错误"},
        )