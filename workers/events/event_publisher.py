from typing import Any

from workers.events.event_bus import EventBus
from workers.events.schemas import EventType


class EventPublisher:
    def __init__(self, event_bus: EventBus | None = None):
        self.event_bus = event_bus or EventBus.create()

    async def publish_vote_cycle_closed(
        self, vote_cycle_id: str, chapter_id: str, closed_at: str, trace_id: str = ""
    ) -> str:
        payload = {
            "vote_cycle_id": vote_cycle_id,
            "chapter_id": chapter_id,
            "closed_at": closed_at,
        }
        return await self.event_bus.publish(
            EventType.VOTE_CYCLE_CLOSED, payload, trace_id=trace_id
        )

    async def publish_vote_result_finalized(
        self,
        vote_cycle_id: str,
        winning_candidate_id: str,
        winning_candidate_name: str,
        total_votes: int,
        finalized_at: str,
        trace_id: str = "",
    ) -> str:
        payload = {
            "vote_cycle_id": vote_cycle_id,
            "winning_candidate_id": winning_candidate_id,
            "winning_candidate_name": winning_candidate_name,
            "total_votes": total_votes,
            "finalized_at": finalized_at,
        }
        return await self.event_bus.publish(
            EventType.VOTE_RESULT_FINALIZED, payload, trace_id=trace_id
        )

    async def publish_generation_request_created(
        self,
        request_id: str,
        vote_cycle_id: str,
        target_type: str,
        region_id: str,
        created_at: str,
        trace_id: str = "",
    ) -> str:
        payload = {
            "request_id": request_id,
            "vote_cycle_id": vote_cycle_id,
            "target_type": target_type,
            "region_id": region_id,
            "created_at": created_at,
        }
        return await self.event_bus.publish(
            EventType.GENERATION_REQUEST_CREATED, payload, trace_id=trace_id
        )

    async def publish_generation_batch_completed(
        self,
        request_id: str,
        generated_objects: list[dict[str, Any]],
        completed_at: str,
        status: str,
        trace_id: str = "",
    ) -> str:
        payload = {
            "request_id": request_id,
            "generated_objects": generated_objects,
            "completed_at": completed_at,
            "status": status,
        }
        return await self.event_bus.publish(
            EventType.GENERATION_BATCH_COMPLETED, payload, trace_id=trace_id
        )

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
        payload = {
            "batch_id": batch_id,
            "request_id": request_id,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "needs_revision_count": needs_revision_count,
            "completed_at": completed_at,
        }
        return await self.event_bus.publish(
            EventType.REVIEW_BATCH_COMPLETED, payload, trace_id=trace_id
        )

    async def publish_content_package_released(
        self,
        content_package_id: str,
        release_mode: str,
        gray_scope: dict[str, Any],
        released_at: str,
        trace_id: str = "",
    ) -> str:
        payload = {
            "content_package_id": content_package_id,
            "release_mode": release_mode,
            "gray_scope": gray_scope,
            "released_at": released_at,
        }
        return await self.event_bus.publish(
            EventType.CONTENT_PACKAGE_RELEASED, payload, trace_id=trace_id
        )

    async def publish_content_package_rolled_back(
        self,
        content_package_id: str,
        rollback_reason: str,
        rolled_back_at: str,
        trace_id: str = "",
    ) -> str:
        payload = {
            "content_package_id": content_package_id,
            "rollback_reason": rollback_reason,
            "rolled_back_at": rolled_back_at,
        }
        return await self.event_bus.publish(
            EventType.CONTENT_PACKAGE_ROLLED_BACK, payload, trace_id=trace_id
        )
