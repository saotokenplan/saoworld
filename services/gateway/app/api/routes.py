import json
import uuid

import httpx
import redis.asyncio as redis
import structlog
from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.config import settings
from app.core.proxy import proxy_request
from app.schemas.events import EventBatchRequest, EventBatchResponse

logger = structlog.get_logger()

router = APIRouter()

_event_bus: redis.Redis | None = None


async def get_event_bus() -> redis.Redis:
    global _event_bus
    if _event_bus is None:
        redis_url = getattr(settings, "redis_url", "redis://localhost:6379")
        _event_bus = redis.from_url(redis_url)
    return _event_bus


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
    version: str


class ServiceHealth(BaseModel):
    service: str
    url: str
    status: str
    latency_ms: float | None = None


class ServicesHealthResponse(BaseModel):
    gateway: HealthResponse
    services: list[ServiceHealth]


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", service=settings.app_name, version=settings.app_version)


@router.get("/health/services", response_model=ServicesHealthResponse)
async def services_health():
    services = [
        {"service": "vote-service", "url": settings.vote_service_url},
        {"service": "world-service", "url": settings.world_service_url},
        {"service": "content-service", "url": settings.content_service_url},
        {"service": "generation-service", "url": settings.generation_service_url},
        {"service": "review-service", "url": settings.review_service_url},
        {"service": "player-service", "url": settings.player_service_url},
        {"service": "ops-service", "url": settings.ops_service_url},
    ]

    results: list[ServiceHealth] = []
    async with httpx.AsyncClient(timeout=5.0) as client:
        for svc in services:
            try:
                import time

                start = time.time()
                response = await client.get(f"{svc['url']}/api/v1/health")
                latency_ms = (time.time() - start) * 1000
                status = "ok" if response.status_code == 200 else "error"
            except Exception:
                status = "unreachable"
                latency_ms = None

            results.append(
                ServiceHealth(
                    service=svc["service"],
                    url=svc["url"],
                    status=status,
                    latency_ms=latency_ms,
                )
            )

    return ServicesHealthResponse(
        gateway=HealthResponse(status="ok", service=settings.app_name, version=settings.app_version),
        services=results,
    )


@router.post("/events/batch", response_model=EventBatchResponse)
async def submit_events(request: Request, body: EventBatchRequest):
    request_id = request.headers.get(settings.request_id_header, f"req_{uuid.uuid4().hex[:12]}")
    trace_id = request.headers.get(settings.trace_id_header)

    logger.info(
        "submit_events_received",
        request_id=request_id,
        trace_id=trace_id,
        event_count=len(body.events),
    )

    try:
        event_bus = await get_event_bus()
        published_count = 0

        for event in body.events:
            event_data = {
                "event_id": str(uuid.uuid4()),
                "event_type": event.event_type,
                "player_id": event.player_id,
                "region_id": event.region_id,
                "occurred_at": event.timestamp.isoformat(),
                "payload": event.payload,
                "trace_id": event.trace_id or trace_id or "",
                "producer": "gateway",
            }

            channel = f"event.{event.event_type}"
            await event_bus.publish(channel, json.dumps(event_data))
            published_count += 1

        logger.info(
            "submit_events_completed",
            request_id=request_id,
            published_count=published_count,
        )

        response = EventBatchResponse(
            request_id=request_id,
            data={"status": "ok", "published_count": published_count},
            meta={"total_events": len(body.events)},
            trace_id=trace_id or "",
        )

        if request_id:
            response.request_id = request_id

        return response

    except Exception as exc:
        logger.error(
            "submit_events_failed",
            request_id=request_id,
            error=str(exc),
        )
        raise


@router.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_all(request: Request):
    return await proxy_request(request)
