import json
from datetime import UTC, datetime
from typing import Any, Optional
from uuid import uuid4

import redis.asyncio as redis

from workers.config import settings
from workers.events.schemas import Event, EventType


class EventBus:
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.broker_url.replace("redis://", "redis://")
        self._redis: Optional[redis.Redis] = None

    async def connect(self) -> None:
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url)

    async def disconnect(self) -> None:
        if self._redis is not None:
            await self._redis.close()
            self._redis = None

    async def publish(
        self,
        event_type: EventType,
        payload: dict[str, Any],
        trace_id: str = "",
        producer: str = "workers",
    ) -> str:
        event = Event(
            event_id=uuid4(),
            event_type=event_type,
            occurred_at=datetime.now(UTC),
            trace_id=trace_id,
            producer=producer,
            payload=payload,
        )

        channel = f"event.{event_type.value}"
        message = event.model_dump_json()

        if self._redis is None:
            await self.connect()

        assert self._redis is not None
        await self._redis.publish(channel, message)
        return str(event.event_id)

    async def subscribe(self, event_types: list[EventType]) -> redis.client.PubSub:
        if self._redis is None:
            await self.connect()

        assert self._redis is not None
        pubsub = self._redis.pubsub()
        channels = [f"event.{event_type.value}" for event_type in event_types]
        await pubsub.subscribe(*channels)
        return pubsub

    async def unsubscribe(self, pubsub: redis.client.PubSub) -> None:
        await pubsub.unsubscribe()

    async def get_message(self, pubsub: redis.client.PubSub, timeout: float = 1.0) -> Optional[Event]:
        message = await pubsub.get_message(timeout=timeout)
        if message and message.get("type") == "message":
            try:
                data = json.loads(message["data"])
                return Event(**data)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    @classmethod
    def create(cls) -> "EventBus":
        return cls(settings.broker_url)
