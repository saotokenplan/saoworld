import uuid
from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ActionType(str, Enum):
    VOTE_CYCLE_CREATE = "vote_cycle_create"
    VOTE_CYCLE_TRANSITION = "vote_cycle_transition"
    CONTENT_RELEASE = "content_release"
    CONTENT_ROLLBACK = "content_rollback"
    REVIEW_APPROVE = "review_approve"
    PLAYER_CREATE = "player_create"
    REGION_UNLOCK = "region_unlock"
    DASHBOARD_VIEW = "dashboard_view"


class ActionStatus(str, Enum):
    PENDING = "pending"
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


class DashboardMetrics(BaseModel):
    total_players: int = 0
    total_vote_cycles: int = 0
    total_votes: int = 0
    total_content_packages: int = 0
    total_regions: int = 0
    live_content_packages: int = 0
    open_vote_cycle: bool = False
    active_generation_requests: int = 0
    pending_review_count: int = 0


class DashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dashboard_id: uuid.UUID
    metrics: DashboardMetrics
    generated_at: datetime


class OpsActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action_id: uuid.UUID
    action_type: ActionType
    resource_type: str
    resource_id: uuid.UUID | None = None
    operator_id: str
    operator_role: str
    status: ActionStatus
    payload_jsonb: dict[str, object] | None = None
    trace_id: str | None = None
    created_at: datetime


class SystemServiceStatus(BaseModel):
    name: str
    status: str = "unknown"
    version: str = "unknown"


class SystemStatusResponse(BaseModel):
    services: list[SystemServiceStatus]
    timestamp: datetime


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
