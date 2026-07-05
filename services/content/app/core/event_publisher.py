from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import settings


class EventPublisher:
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or "redis://localhost:6379/0"
        self._redis: Optional[redis.Redis] = None

    async def connect(self) -> None:
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url)

    async def disconnect(self) -> None:
        if self._redis is not None:
            await self._redis.close()
            self._redis = None

    async def publish(self, event_type: str, payload: dict, trace_id: str = "") -> str:
        import json
        from datetime import datetime, timezone
        from uuid import uuid4

        event_id: str = str(uuid4())
        event = {
            "event_id": event_id,
            "event_type": event_type,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id,
            "producer": "content-service",
            "payload": payload,
        }

        channel = f"event.{event_type}"
        message = json.dumps(event)

        if self._redis is None:
            await self.connect()

        assert self._redis is not None
        await self._redis.publish(channel, message)
        return event_id

    async def publish_content_package_released(
        self,
        content_package_id: str,
        release_mode: str,
        gray_scope: dict[str, Any],
        released_at: str,
        trace_id: str = "",
    ) -> str:
        return await self.publish(
            "content.package.released",
            {
                "content_package_id": content_package_id,
                "release_mode": release_mode,
                "gray_scope": gray_scope,
                "released_at": released_at,
            },
            trace_id=trace_id,
        )

    async def publish_content_package_rolled_back(
        self,
        content_package_id: str,
        rollback_reason: str,
        rolled_back_at: str,
        trace_id: str = "",
    ) -> str:
        return await self.publish(
            "content.package.rolled_back",
            {
                "content_package_id": content_package_id,
                "rollback_reason": rollback_reason,
                "rolled_back_at": rolled_back_at,
            },
            trace_id=trace_id,
        )


event_publisher = EventPublisher()