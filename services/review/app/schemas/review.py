import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ReviewResult(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


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


class ReviewEfficiencyResponse(BaseModel):
    """WP3 ops 看板三字段：审核效率派生指标（数据源为 review 服务 Prometheus 指标）。"""

    auto_pass_rate: float | None = None
    manual_intervention_rate: float | None = None
    review_p95_minutes: float | None = None
    raw: dict[str, Any] | None = None


class ReviewRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    review_id: uuid.UUID
    object_id: uuid.UUID
    object_type: str
    review_type: str
    result: ReviewResult
    risk_level: RiskLevel
    quality_score: float | None = None
    detail: dict[str, object] | None = None
    operator_id: str | None = None
    operator_role: str | None = None
    reason: str | None = None
    trace_id: str
    created_at: datetime
    updated_at: datetime


class ReviewRecordListResponse(BaseModel):
    reviews: list[ReviewRecordResponse]
    total: int


class CreateReviewRequest(BaseModel):
    object_id: uuid.UUID
    object_type: str = Field(min_length=1, max_length=64)
    review_type: str = Field(min_length=1, max_length=32)
    trace_id: str = Field(min_length=1, max_length=128)
    quality_score: float | None = Field(default=None, ge=0, le=1)
    detail: dict[str, object] | None = None
    result: ReviewResult = ReviewResult.PENDING
    risk_level: RiskLevel = RiskLevel.LOW


class CreateReviewResponse(BaseModel):
    review_id: uuid.UUID
    object_id: uuid.UUID
    result: ReviewResult
    request_id_: str
    trace_id: str | None = None


class UpdateReviewResultRequest(BaseModel):
    result: ReviewResult
    risk_level: RiskLevel | None = None
    reason: str | None = None


class UpdateReviewResultResponse(BaseModel):
    review_id: uuid.UUID
    object_id: uuid.UUID
    result: ReviewResult
    risk_level: RiskLevel
    request_id_: str
    trace_id: str | None = None


class ApproveReviewRequest(BaseModel):
    reason: str | None = None


class ApproveReviewResponse(BaseModel):
    object_id: uuid.UUID
    result: ReviewResult
    request_id_: str
    trace_id: str | None = None


class RejectReviewRequest(BaseModel):
    reason: str | None = None
    risk_level: RiskLevel = RiskLevel.MEDIUM


class RejectReviewResponse(BaseModel):
    object_id: uuid.UUID
    result: ReviewResult
    risk_level: RiskLevel
    request_id_: str
    trace_id: str | None = None


class AutoReviewRequest(BaseModel):
    object_id: uuid.UUID
    object_type: str = Field(min_length=1, max_length=64)
    object_payload: dict[str, object]
    quality_score: float | None = Field(default=None, ge=0, le=1)
    trace_id: str = Field(min_length=1, max_length=128)
    # WP4：内容包引用。携带时，自动审核通过将发布 review.auto.approved 事件，
    # 由 workers 侧串联至发布队列；缺省时降级为「仅审核不发布」。
    content_package_id: uuid.UUID | None = None


class AutoReviewRuleResult(BaseModel):
    rule: str
    result: str | None
    error: str | None = None


class AutoReviewResponse(BaseModel):
    object_id: uuid.UUID
    auto_result: str
    reason: str
    is_automatic: bool
    rule_results: list[AutoReviewRuleResult]
    request_id_: str
    trace_id: str | None = None
