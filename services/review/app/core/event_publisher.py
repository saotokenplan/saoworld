from typing import Optional

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

        event = {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id,
            "producer": "review-service",
            "payload": payload,
        }

        channel = f"event.{event_type}"
        message = json.dumps(event)

        if self._redis is None:
            await self.connect()

        assert self._redis is not None
        await self._redis.publish(channel, message)
        return str(event["event_id"])

    async def publish_review_batch_completed(
        self,
        batch_id: str,
        request_id: str,
        approved_count: int,
        rejected_count: int,
        needs_revision_count: int,
        completed_at: str,
        trace_id: str = "",
    ) -> str:
        return await self.publish(
            "review.batch.completed",
            {
                "batch_id": batch_id,
                "request_id": request_id,
                "approved_count": approved_count,
                "rejected_count": rejected_count,
                "needs_revision_count": needs_revision_count,
                "completed_at": completed_at,
            },
            trace_id=trace_id,
        )


event_publisher = EventPublisher()