import uuid
from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PackageStatus(str, Enum):
    PACKAGED = "packaged"
    GRAY = "gray"
    LIVE = "live"
    ARCHIVED = "archived"
    ROLLED_BACK = "rolled_back"


class ReleaseMode(str, Enum):
    GRAY = "gray"
    FULL = "full"


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


class ContentPackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    content_package_id: uuid.UUID
    chapter_id: str
    region_id: uuid.UUID | None = None
    package_version: str
    source_vote_cycle_id: uuid.UUID | None = None
    source_request_id: uuid.UUID | None = None
    title: str
    summary: str | None = None
    status: PackageStatus
    gray_scope: dict[str, object] | None = None
    payload: dict[str, object]
    schema_version: int
    released_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ContentPackageListResponse(BaseModel):
    packages: list[ContentPackageResponse]
    total: int


class CreatePackageRequest(BaseModel):
    chapter_id: str = Field(min_length=1, max_length=64)
    region_id: uuid.UUID | None = None
    package_version: str = Field(min_length=1, max_length=32)
    source_vote_cycle_id: uuid.UUID | None = None
    source_request_id: uuid.UUID | None = None
    title: str = Field(min_length=1, max_length=512)
    summary: str | None = None
    payload: dict[str, object]
    schema_version: int = 1


class CreatePackageResponse(BaseModel):
    content_package_id: uuid.UUID
    chapter_id: str
    title: str
    status: PackageStatus
    package_version: str
    request_id: str
    trace_id: str | None = None


class ReleasePackageRequest(BaseModel):
    release_mode: ReleaseMode
    gray_scope: dict[str, object] | None = None
    reason: str = Field(min_length=1)


class ReleasePackageResponse(BaseModel):
    content_package_id: uuid.UUID
    status: PackageStatus
    release_mode: ReleaseMode
    request_id: str
    trace_id: str | None = None


class RollbackPackageRequest(BaseModel):
    target_version: str = Field(min_length=1, max_length=32)
    reason: str = Field(min_length=1)


class RollbackPackageResponse(BaseModel):
    content_package_id: uuid.UUID
    status: PackageStatus
    target_version: str
    request_id: str
    trace_id: str | None = None
