import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# --- 状态枚举 ---

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


# --- 统一响应 Envelope ---

class EnvelopeResponse(BaseModel):
    """统一成功响应包装"""
    request_id: str
    data: Any
    meta: dict[str, Any] | None = None
    trace_id: str | None = None


class PaginationMeta(BaseModel):
    """分页元数据"""
    total: int
    limit: int
    offset: int


# --- 错误响应 ---

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
    trace_id: str | None = None


# --- 业务数据模型 ---

class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: uuid.UUID
    title: str
    summary: str
    description: str | None = None
    vote_count: int = 0
    status: VoteCandidateStatus


class CurrentVoteData(BaseModel):
    """GET /votes/current 的 data 字段"""
    vote_cycle_id: uuid.UUID
    chapter_id: str
    status: VoteCycleStatus
    starts_at: datetime
    ends_at: datetime
    candidates: list[CandidateResponse]
    has_voted: bool = False
    my_vote_candidate_id: uuid.UUID | None = None


class VoteSubmitData(BaseModel):
    """POST /votes/submit 的 data 字段"""
    vote_id: uuid.UUID
    vote_cycle_id: uuid.UUID
    candidate_id: uuid.UUID
    submitted_at: datetime


class VoteHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vote_id: uuid.UUID
    vote_cycle_id: uuid.UUID
    candidate_id: uuid.UUID
    candidate_title: str
    weight: float
    created_at: datetime


class VoteHistoryData(BaseModel):
    """GET /votes/history 的 data 字段"""
    player_id: uuid.UUID
    votes: list[VoteHistoryItem]


# --- 请求模型 ---

class VoteSubmitRequest(BaseModel):
    candidate_id: uuid.UUID
    device_fingerprint_hash: str = Field(min_length=1, max_length=128)
    weight: float = Field(default=1.0, gt=0, le=10.0)


# --- 运营接口模型 ---

class CandidateInput(BaseModel):
    """创建投票周期时的候选项输入"""
    title: str = Field(min_length=1, max_length=512)
    summary: str = Field(min_length=1)
    description: str | None = None
    region_scope: list[str] = Field(default_factory=list)
    risk_tags: list[str] = Field(default_factory=list)


class CreateVoteCycleRequest(BaseModel):
    """POST /ops/vote-cycles 请求体"""
    chapter_id: str = Field(min_length=1, max_length=64)
    starts_at: datetime
    ends_at: datetime
    created_by: str = Field(min_length=1, max_length=128)
    created_reason: str = Field(min_length=1)
    candidates: list[CandidateInput] = Field(min_length=2)


class VoteCycleData(BaseModel):
    """创建投票周期返回的 data 字段"""
    vote_cycle_id: uuid.UUID
    chapter_id: str
    status: VoteCycleStatus
    starts_at: datetime
    ends_at: datetime
    candidates: list[CandidateResponse]


# --- 健康检查 ---

class HealthResponse(BaseModel):
    service: str
    version: str
    status: str = "ok"
