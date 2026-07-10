import uuid
from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class RegionStatus(str, Enum):
    LOCKED = "locked"
    ACTIVE = "active"
    UNSTABLE = "unstable"
    ARCHIVED = "archived"


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


class PaginatedMeta(BaseModel):
    total: int
    limit: int
    offset: int


class EnvelopeResponse(BaseModel, Generic[T]):
    request_id: str
    data: T
    meta: PaginatedMeta | None = None
    trace_id: str | None = None


class RegionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    region_id: uuid.UUID
    chapter_id: str
    title: str
    summary: str | None = None
    status: RegionStatus
    visible: bool
    unlock_condition: dict[str, object] | None = None
    created_at: datetime
    updated_at: datetime


class RegionListResponse(BaseModel):
    regions: list[RegionResponse]
    total: int


class CreateRegionRequest(BaseModel):
    chapter_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=256)
    summary: str | None = None
    status: RegionStatus = RegionStatus.LOCKED
    visible: bool = False
    unlock_condition: dict[str, object] | None = None


class CreateRegionResponse(BaseModel):
    region_id: uuid.UUID
    chapter_id: str
    title: str
    status: RegionStatus
    visible: bool
    request_id: str
    trace_id: str | None = None


class UpdateRegionStatusRequest(BaseModel):
    status: RegionStatus
    reason: str = Field(min_length=1)


class UpdateRegionStatusResponse(BaseModel):
    region_id: uuid.UUID
    status: RegionStatus
    request_id: str
    trace_id: str | None = None


class WorldSkeletonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skeleton_id: uuid.UUID
    world_version: str
    chapter_id: str
    regions: dict[str, object]
    factions: dict[str, object]
    reserved_characters: dict[str, object] | None = None
    forbidden_tags: list[str]
    reward_limits: dict[str, object] | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CreateWorldSkeletonRequest(BaseModel):
    world_version: str = Field(min_length=1, max_length=64)
    chapter_id: str = Field(min_length=1, max_length=64)
    regions: dict[str, object] = Field(min_length=1)
    factions: dict[str, object] = Field(min_length=1)
    reserved_characters: dict[str, object] | None = None
    forbidden_tags: list[str] = Field(min_length=1)
    reward_limits: dict[str, object] | None = None
    is_active: bool = True


class CreateWorldSkeletonResponse(BaseModel):
    skeleton_id: uuid.UUID
    world_version: str
    chapter_id: str
    is_active: bool
    request_id: str
    trace_id: str | None = None


class NpcDialogueEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trigger: str | None = None
    text: str
    conditions: dict[str, object] | None = None


class NpcResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    npc_id: uuid.UUID
    npc_key: str
    chapter_id: str
    name: str
    title: str | None = None
    faction_key: str | None = None
    role: str | None = None
    location_key: str | None = None
    description: str | None = None
    personality: list[str] | None = None
    dialogues: list[dict[str, object]] | None = None
    related_quests: list[str] | None = None
    rewards: dict[str, object] | None = None
    min_reputation: int = 0
    interaction_restrictions: dict[str, object] | None = None
    created_at: datetime
    updated_at: datetime


class NpcListResponse(BaseModel):
    npcs: list[NpcResponse]
    total: int


class CreateNpcRequest(BaseModel):
    npc_key: str = Field(min_length=1, max_length=128, pattern=r"^[a-zA-Z0-9_\-]+$")
    chapter_id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    title: str | None = Field(default=None, max_length=128)
    faction_key: str | None = Field(default=None, max_length=128)
    role: str | None = Field(default=None, max_length=64)
    location_key: str | None = Field(default=None, max_length=128)
    description: str | None = None
    personality: list[str] | None = None
    dialogues: list[dict[str, object]] | None = None
    related_quests: list[str] | None = None
    rewards: dict[str, object] | None = None
    min_reputation: int = Field(default=0, ge=0)
    interaction_restrictions: dict[str, object] | None = None


class CreateNpcResponse(BaseModel):
    npc_id: uuid.UUID
    npc_key: str
    chapter_id: str
    name: str
    request_id: str
    trace_id: str | None = None


class QuestType(str, Enum):
    MAIN = "main"
    SIDE = "side"
    EVENT = "event"
    DAILY = "daily"


class QuestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    quest_id: uuid.UUID
    quest_key: str
    chapter_id: str
    title: str
    description: str | None = None
    quest_type: QuestType
    region_key: str | None = None
    start_npc_key: str | None = None
    end_npc_key: str | None = None
    prerequisites: list[str] | None = None
    objectives: list[dict[str, object]]
    rewards: dict[str, object] | None = None
    failure_condition: dict[str, object] | None = None
    min_reputation: int = 0
    required_reputation_level: str | None = None
    created_at: datetime
    updated_at: datetime


class QuestListResponse(BaseModel):
    quests: list[QuestResponse]
    total: int


class CreateQuestRequest(BaseModel):
    quest_key: str = Field(min_length=1, max_length=128, pattern=r"^[a-zA-Z0-9_\-]+$")
    chapter_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=256)
    description: str | None = None
    quest_type: QuestType
    region_key: str | None = Field(default=None, max_length=128)
    start_npc_key: str | None = Field(default=None, max_length=128)
    end_npc_key: str | None = Field(default=None, max_length=128)
    prerequisites: list[str] | None = None
    objectives: list[dict[str, object]] = Field(min_length=1)
    rewards: dict[str, object] | None = None
    failure_condition: dict[str, object] | None = None
    min_reputation: int = Field(default=0, ge=0)
    required_reputation_level: str | None = Field(default=None, max_length=32)


class CreateQuestResponse(BaseModel):
    quest_id: uuid.UUID
    quest_key: str
    chapter_id: str
    title: str
    quest_type: QuestType
    request_id: str
    trace_id: str | None = None
