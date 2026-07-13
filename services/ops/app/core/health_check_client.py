import asyncio
from typing import Dict, Tuple

import httpx

from app.core.config import settings


SERVICE_CONFIG: Dict[str, str] = {
    "vote-service": settings.vote_service_url,
    "world-service": settings.world_service_url,
    "content-service": settings.content_service_url,
    "generation-service": settings.generation_service_url,
    "review-service": settings.review_service_url,
    "gateway-service": settings.gateway_service_url,
    "player-service": settings.player_service_url,
    "ops-service": settings.ops_service_url,
}


async def check_service_health(service_name: str, base_url: str) -> Tuple[str, str]:
    health_url = f"{base_url}{settings.api_v1_prefix}/health"

    async with httpx.AsyncClient(timeout=settings.health_check_timeout) as client:
        try:
            response = await client.get(health_url)
            if response.status_code == 200:
                data = await response.json()
                version = data.get("data", {}).get("version", "unknown")
                return "ok", version
            return "unavailable", "unknown"
        except (httpx.HTTPError, asyncio.TimeoutError):
            return "unavailable", "unknown"


async def check_all_services_health() -> Dict[str, Tuple[str, str]]:
    tasks = [
        check_service_health(name, url)
        for name, url in SERVICE_CONFIG.items()
    ]
    results = await asyncio.gather(*tasks)
    return dict(zip(SERVICE_CONFIG.keys(), results))
