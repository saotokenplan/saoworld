import uuid
from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class VoteCycleStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    OPEN = "open"
    CLOSED = "closed"
    FINALIZED = "finalized"


class VoteCandidateStatus(str, Enum):
    ACTIVE = "active"
    WITHDRAWN = "withdrawn"
    SELECTED = "selected"


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


class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: uuid.UUID
    title: str
    summary: str
    description: str | None = None
    vote_count: int = 0
    status: VoteCandidateStatus


class CurrentVoteResponse(BaseModel):
    vote_cycle_id: uuid.UUID
    chapter_id: str
    status: VoteCycleStatus
    starts_at: datetime
    ends_at: datetime
    candidates: list[CandidateResponse]
    has_voted: bool = False
    my_vote_candidate_id: uuid.UUID | None = None


class VoteSubmitRequest(BaseModel):
    candidate_id: uuid.UUID
    device_fingerprint_hash: str = Field(min_length=1, max_length=128)
    weight: float = Field(default=1.0, gt=0.0, le=10.0)


class VoteSubmitResponse(BaseModel):
    vote_id: uuid.UUID
    vote_cycle_id: uuid.UUID
    candidate_id: uuid.UUID
    submitted_at: datetime
    weight: float | None = None
    weight_multiplier: float | None = None
    contribution_points: int | None = None
    request_id: str
    trace_id: str | None = None


class VoteHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vote_id: uuid.UUID
    vote_cycle_id: uuid.UUID
    candidate_id: uuid.UUID
    candidate_title: str
    weight: float
    created_at: datetime


class VoteHistoryResponse(BaseModel):
    player_id: uuid.UUID
    votes: list[VoteHistoryItem]
    total: int


class HealthResponse(BaseModel):
    service: str
    version: str
    status: str = "ok"


# --- 运营写接口 Schema ---


class CandidateInput(BaseModel):
    """创建投票周期时的候选项输入"""

    title: str = Field(min_length=1, max_length=512)
    summary: str = Field(min_length=1)
    description: str | None = None
    region_scope: list[str] = Field(default_factory=list)
    risk_tags: list[str] = Field(default_factory=list)
    generated_params: dict[str, object] | None = None


class CreateVoteCycleRequest(BaseModel):
    """创建投票周期请求体"""

    chapter_id: str = Field(min_length=1, max_length=64)
    starts_at: datetime
    ends_at: datetime
    candidates: list[CandidateInput] = Field(min_length=2)
    reason: str = Field(min_length=1)


class VoteCycleDetailResponse(BaseModel):
    """投票周期详情响应"""

    model_config = ConfigDict(from_attributes=True)

    vote_cycle_id: uuid.UUID
    chapter_id: str
    status: VoteCycleStatus
    starts_at: datetime
    ends_at: datetime
    created_by: str
    created_reason: str
    finalized_at: datetime | None = None
    winning_candidate_id: uuid.UUID | None = None
    candidates: list[CandidateResponse] = []
    created_at: datetime
    updated_at: datetime


class CreateVoteCycleResponse(BaseModel):
    """创建投票周期响应"""

    vote_cycle_id: uuid.UUID
    chapter_id: str
    status: VoteCycleStatus
    starts_at: datetime
    ends_at: datetime
    candidates: list[CandidateResponse]
    request_id: str
    trace_id: str | None = None


class TransitionVoteCycleRequest(BaseModel):
    """投票周期状态变更请求体"""

    reason: str = Field(min_length=1)


class TransitionVoteCycleResponse(BaseModel):
    """投票周期状态变更响应"""

    vote_cycle_id: uuid.UUID
    status: VoteCycleStatus
    winning_candidate_id: uuid.UUID | None = None
    request_id: str
    trace_id: str | None = None


# --- 通用响应 Envelope ---


class PaginatedMeta(BaseModel):
    """分页元信息。"""

    total: int
    limit: int
    offset: int


class EnvelopeResponse(BaseModel, Generic[T]):
    """统一响应 envelope，所有成功响应必须使用此格式。"""

    request_id: str
    data: T
    meta: PaginatedMeta | None = None
    trace_id: str | None = None
