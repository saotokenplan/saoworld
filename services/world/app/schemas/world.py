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
