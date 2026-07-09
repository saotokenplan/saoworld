import uuid
from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class QuestStatus(str, Enum):
    AVAILABLE = "available"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class ErrorDetail(BaseModel):
    location: str
    field: str
    issue: str
    rejected_value: object | None = None


class ErrorResponse(BaseModel):
    code: str
    message: str
    request_id: str
    details: list[ErrorDetail] | None = None


class HealthResponse(BaseModel):
    service: str
    version: str
    status: str = "ok"


class PlayerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    player_id: uuid.UUID
    display_name: str
    chapter_id: str | None = None
    reputation_snapshot: dict | None = None
    progress_jsonb: dict | None = None
    created_at: datetime
    updated_at: datetime


class CreatePlayerRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=128)
    chapter_id: str | None = None


class UpdatePlayerRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=128)
    chapter_id: str | None = None


class PlayerQuestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    player_quest_id: uuid.UUID
    quest_id: str
    status: QuestStatus
    objectives_jsonb: dict | None = None
    rewards_jsonb: dict | None = None
    created_at: datetime
    updated_at: datetime


class AcceptQuestRequest(BaseModel):
    pass


class UpdateQuestProgressRequest(BaseModel):
    objectives: dict[str, object] = Field(default_factory=dict)


class CompleteQuestRequest(BaseModel):
    pass


class FailQuestRequest(BaseModel):
    pass


class CreatePlayerQuestRequest(BaseModel):
    quest_id: str = Field(min_length=1, max_length=128)
    status: QuestStatus = QuestStatus.AVAILABLE
    objectives_jsonb: dict | None = None
    rewards_jsonb: dict | None = None


class UpdateQuestStatusRequest(BaseModel):
    status: QuestStatus


class PlayerRegionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    player_region_id: uuid.UUID
    region_id: str
    unlocked_at: datetime | None = None
    reputation: int = 0
    created_at: datetime


class PaginatedMeta(BaseModel):
    total: int
    limit: int
    offset: int


class EnvelopeResponse(BaseModel, Generic[T]):
    request_id: str
    data: T
    meta: PaginatedMeta | None = None
    trace_id: str | None = None