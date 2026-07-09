import uuid
from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class GenerationRequestStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED_RETRYABLE = "failed_retryable"
    FAILED_PERMANENT = "failed_permanent"


class GeneratedObjectStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


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


class GenerationRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    request_id: uuid.UUID
    vote_cycle_id: uuid.UUID | None = None
    source_candidate_id: uuid.UUID | None = None
    template_id: str
    input_payload: dict[str, object]
    status: GenerationRequestStatus
    retry_count: int
    max_retries: int
    error_message: str | None = None
    trace_id: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    cost_usd: float | None = None
    created_at: datetime
    updated_at: datetime


class GenerationRequestListResponse(BaseModel):
    requests: list[GenerationRequestResponse]
    total: int


class CreateGenerationRequestRequest(BaseModel):
    vote_cycle_id: uuid.UUID | None = None
    source_candidate_id: uuid.UUID | None = None
    template_id: str = Field(min_length=1, max_length=128)
    input_payload: dict[str, object]
    trace_id: str = Field(min_length=1, max_length=128)


class CreateGenerationRequestResponse(BaseModel):
    request_id: uuid.UUID
    template_id: str
    status: GenerationRequestStatus
    request_id_: str
    trace_id: str | None = None


class UpdateGenerationStatusRequest(BaseModel):
    status: GenerationRequestStatus
    error_message: str | None = None


class UpdateGenerationStatusResponse(BaseModel):
    request_id: uuid.UUID
    status: GenerationRequestStatus
    request_id_: str
    trace_id: str | None = None


class GeneratedObjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    object_id: uuid.UUID
    request_id: uuid.UUID
    object_type: str
    schema_version: int
    object_payload: dict[str, object]
    quality_score: float | None = None
    status: GeneratedObjectStatus
    created_at: datetime
    updated_at: datetime


class GeneratedObjectListResponse(BaseModel):
    objects: list[GeneratedObjectResponse]
    total: int


class CreateGeneratedObjectRequest(BaseModel):
    request_id: uuid.UUID
    object_type: str = Field(min_length=1, max_length=64)
    schema_version: int = 1
    object_payload: dict[str, object]
    quality_score: float | None = Field(default=None, ge=0, le=1)


class CreateGeneratedObjectResponse(BaseModel):
    object_id: uuid.UUID
    request_id: uuid.UUID
    object_type: str
    status: GeneratedObjectStatus
    quality_score: float | None
    request_id_: str
    trace_id: str | None = None


class UpdateObjectStatusRequest(BaseModel):
    status: GeneratedObjectStatus


class UpdateObjectStatusResponse(BaseModel):
    object_id: uuid.UUID
    status: GeneratedObjectStatus
    request_id_: str
    trace_id: str | None = None


class GenerationCostSummary(BaseModel):
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_cost_usd: float
    daily_used_tokens: int
    monthly_used_tokens: int
    daily_budget_tokens: int
    monthly_budget_tokens: int
    daily_usage_ratio: float
    monthly_usage_ratio: float
    should_alert: bool
    should_pause: bool


class GenerationCostResponse(BaseModel):
    cost_summary: GenerationCostSummary
    period: str
    start_date: datetime | None = None
    end_date: datetime | None = None


class CostQueryRequest(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None
    period: str = Field(default="daily", pattern="^(daily|monthly|custom)$")
