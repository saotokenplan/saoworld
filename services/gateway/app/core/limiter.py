import asyncio
import time
from collections import defaultdict

import structlog
from fastapi import HTTPException, Request

from app.core.config import settings
from app.core.metrics import record_rate_limit_hit

logger = structlog.get_logger()


class RateLimiter:
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.client_requests: dict[str, list[float]] = defaultdict(list)
        self.lock = asyncio.Lock()

    async def check(self, client_id: str) -> bool:
        async with self.lock:
            now = time.time()
            self.client_requests[client_id] = [
                t for t in self.client_requests[client_id] if now - t < 60
            ]

            if len(self.client_requests[client_id]) >= self.requests_per_minute:
                return False

            self.client_requests[client_id].append(now)
            return True


rate_limiter = RateLimiter(settings.rate_limit_requests_per_minute)


async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/v1/health"):
        return await call_next(request)

    if not hasattr(request.state, "player_id"):
        return await call_next(request)

    client_id = request.state.player_id

    allowed = await rate_limiter.check(client_id)
    if not allowed:
        logger.warning("rate_limit_exceeded", client_id=client_id)
        # 业务指标：限流触发计数
        record_rate_limit_hit()
        raise HTTPException(
            status_code=429,
            detail={"code": "RATE_LIMIT_EXCEEDED", "message": "请求过于频繁，请稍后再试"},
        )

    return await call_next(request)
