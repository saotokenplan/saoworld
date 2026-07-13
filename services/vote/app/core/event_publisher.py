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
            "producer": "vote-service",
            "payload": payload,
        }

        channel = f"event.{event_type}"
        message = json.dumps(event)

        if self._redis is None:
            try:
                await self.connect()
            except Exception:
                return str(event["event_id"])

        if self._redis is None:
            return str(event["event_id"])

        try:
            await self._redis.publish(channel, message)
        except Exception:
            pass

        return str(event["event_id"])

    async def publish_vote_cycle_closed(
        self, vote_cycle_id: str, chapter_id: str, closed_at: str, trace_id: str = ""
    ) -> str:
        return await self.publish(
            "vote.cycle.closed",
            {
                "vote_cycle_id": vote_cycle_id,
                "chapter_id": chapter_id,
                "closed_at": closed_at,
            },
            trace_id=trace_id,
        )

    async def publish_vote_result_finalized(
        self,
        vote_cycle_id: str,
        chapter_id: str,
        winning_candidate_id: str,
        winning_candidate_name: str,
        total_votes: int,
        finalized_at: str,
        generated_params: dict | None = None,
        region_scope: list | None = None,
        trace_id: str = "",
    ) -> str:
        payload = {
            "vote_cycle_id": vote_cycle_id,
            "chapter_id": chapter_id,
            "winning_candidate_id": winning_candidate_id,
            "winning_candidate_name": winning_candidate_name,
            "total_votes": total_votes,
            "finalized_at": finalized_at,
        }
        if generated_params is not None:
            payload["generated_params"] = generated_params
        if region_scope is not None:
            payload["region_scope"] = region_scope
        return await self.publish(
            "vote.result.finalized",
            payload,
            trace_id=trace_id,
        )

    async def publish_vote_progress_updated(
        self,
        vote_cycle_id: str,
        chapter_id: str,
        total_votes: int,
        total_weighted_votes: float,
        leading_candidate_id: str,
        candidates: list[dict],
        trace_id: str = "",
    ) -> str:
        return await self.publish(
            "vote.progress.updated",
            {
                "vote_cycle_id": vote_cycle_id,
                "chapter_id": chapter_id,
                "total_votes": total_votes,
                "total_weighted_votes": total_weighted_votes,
                "leading_candidate_id": leading_candidate_id,
                "candidates": candidates,
            },
            trace_id=trace_id,
        )


event_publisher = EventPublisher()