import httpx
import structlog
from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.config import settings
from app.core.proxy import proxy_request

logger = structlog.get_logger()

router = APIRouter()


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


@router.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_all(request: Request):
    return await proxy_request(request)