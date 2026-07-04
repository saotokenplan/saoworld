from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field


class EventType(str, Enum):
    VOTE_CYCLE_CLOSED = "vote.cycle.closed"
    VOTE_RESULT_FINALIZED = "vote.result.finalized"
    GENERATION_REQUEST_CREATED = "generation.request.created"
    GENERATION_BATCH_COMPLETED = "generation.batch.completed"
    REVIEW_BATCH_COMPLETED = "review.batch.completed"
    CONTENT_PACKAGE_RELEASED = "content.package.released"
    CONTENT_PACKAGE_ROLLED_BACK = "content.package.rolled_back"


class Event(BaseModel):
    event_id: UUID = Field(default_factory=lambda: UUID(int=0))
    event_type: EventType
    occurred_at: datetime = Field(default_factory=lambda: datetime.fromtimestamp(0))
    trace_id: str = ""
    producer: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class VoteCycleClosedEvent(Event):
    event_type: EventType = EventType.VOTE_CYCLE_CLOSED
    payload: dict[str, Any] = Field(
        default_factory=lambda: {
            "vote_cycle_id": "",
            "chapter_id": "",
            "closed_at": "",
        }
    )


class VoteResultFinalizedEvent(Event):
    event_type: EventType = EventType.VOTE_RESULT_FINALIZED
    payload: dict[str, Any] = Field(
        default_factory=lambda: {
            "vote_cycle_id": "",
            "winning_candidate_id": "",
            "winning_candidate_name": "",
            "total_votes": 0,
            "finalized_at": "",
        }
    )


class GenerationRequestCreatedEvent(Event):
    event_type: EventType = EventType.GENERATION_REQUEST_CREATED
    payload: dict[str, Any] = Field(
        default_factory=lambda: {
            "request_id": "",
            "vote_cycle_id": "",
            "target_type": "",
            "region_id": "",
            "created_at": "",
        }
    )


class GenerationBatchCompletedEvent(Event):
    event_type: EventType = EventType.GENERATION_BATCH_COMPLETED
    payload: dict[str, Any] = Field(
        default_factory=lambda: {
            "request_id": "",
            "generated_objects": [],
            "completed_at": "",
            "status": "",
        }
    )


class ReviewBatchCompletedEvent(Event):
    event_type: EventType = EventType.REVIEW_BATCH_COMPLETED
    payload: dict[str, Any] = Field(
        default_factory=lambda: {
            "batch_id": "",
            "request_id": "",
            "approved_count": 0,
            "rejected_count": 0,
            "needs_revision_count": 0,
            "completed_at": "",
        }
    )


class ContentPackageReleasedEvent(Event):
    event_type: EventType = EventType.CONTENT_PACKAGE_RELEASED
    payload: dict[str, Any] = Field(
        default_factory=lambda: {
            "content_package_id": "",
            "release_mode": "",
            "gray_scope": {},
            "released_at": "",
        }
    )


class ContentPackageRolledBackEvent(Event):
    event_type: EventType = EventType.CONTENT_PACKAGE_ROLLED_BACK
    payload: dict[str, Any] = Field(
        default_factory=lambda: {
            "content_package_id": "",
            "rollback_reason": "",
            "rolled_back_at": "",
        }
    )