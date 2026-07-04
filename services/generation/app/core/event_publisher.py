from typing import Any, Optional

import redis.asyncio as redis

from services.generation.app.core.config import settings


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
        from datetime import datetime
        from uuid import uuid4

        event = {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "occurred_at": datetime.utcnow().isoformat(),
            "trace_id": trace_id,
            "producer": "generation-service",
            "payload": payload,
        }

        channel = f"event.{event_type}"
        message = json.dumps(event)

        if self._redis is None:
            await self.connect()

        await self._redis.publish(channel, message)
        return event["event_id"]

    async def publish_generation_request_created(
        self,
        request_id: str,
        vote_cycle_id: str,
        target_type: str,
        region_id: str,
        created_at: str,
        trace_id: str = "",
    ) -> str:
        return await self.publish(
            "generation.request.created",
            {
                "request_id": request_id,
                "vote_cycle_id": vote_cycle_id,
                "target_type": target_type,
                "region_id": region_id,
                "created_at": created_at,
            },
            trace_id=trace_id,
        )

    async def publish_generation_batch_completed(
        self,
        request_id: str,
        generated_objects: list[dict[str, Any]],
        completed_at: str,
        status: str,
        trace_id: str = "",
    ) -> str:
        return await self.publish(
            "generation.batch.completed",
            {
                "request_id": request_id,
                "generated_objects": generated_objects,
                "completed_at": completed_at,
                "status": status,
            },
            trace_id=trace_id,
        )


event_publisher = EventPublisher()