from typing import Optional

import redis.asyncio as redis


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
        content_package_id: str | None = None,
        trace_id: str = "",
    ) -> str:
        """人工审核批次完成事件。

        WP4：负载补齐 `content_package_id`。消费侧
        `workers.events.handlers.handle_review_batch_completed` 以
        `content_package_id and approved_count > 0` 为守卫触发全量复审，
        此前该键从未写入，守卫恒为假、复审链路实际断开。
        该字段可选，缺省时保持「仅审核不复审」的既有行为。
        """
        return await self.publish(
            "review.batch.completed",
            {
                "batch_id": batch_id,
                "request_id": request_id,
                "content_package_id": content_package_id,
                "approved_count": approved_count,
                "rejected_count": rejected_count,
                "needs_revision_count": needs_revision_count,
                "completed_at": completed_at,
            },
            trace_id=trace_id,
        )

    async def publish_review_auto_approved(
        self,
        object_id: str,
        object_type: str,
        content_package_id: str,
        approved_at: str,
        quality_score: float | None = None,
        risk_level: str = "low",
        release_mode: str = "gray",
        trace_id: str = "",
    ) -> str:
        """WP4：自动审核通过事件。

        由 workers 侧 `handle_review_auto_approved` 消费，将内容包送入发布队列。
        `risk_level` 非 low 时下游不会自动入队，留人工确认。
        """
        return await self.publish(
            "review.auto.approved",
            {
                "object_id": object_id,
                "object_type": object_type,
                "content_package_id": content_package_id,
                "quality_score": quality_score,
                "risk_level": risk_level,
                "release_mode": release_mode,
                "approved_at": approved_at,
            },
            trace_id=trace_id,
        )


event_publisher = EventPublisher()
