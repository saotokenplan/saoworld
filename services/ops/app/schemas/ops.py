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


class EconomicOverview(BaseModel):
    total_trades: int = 0
    completed_trades: int = 0
    trade_completion_rate: float = 0.0
    total_auctions: int = 0
    active_auctions: int = 0
    sold_auctions: int = 0
    total_wallets: int = 0
    total_gold_supply: int = 0
    total_transactions: int = 0


class TradeStatsItem(BaseModel):
    date: str
    total_trades: int
    completed_trades: int
    cancelled_trades: int
    completion_rate: float


class AuctionStatsItem(BaseModel):
    date: str
    total_listings: int
    sold_listings: int
    active_listings: int
    total_volume: int
    sell_through_rate: float


class WalletStatsItem(BaseModel):
    date: str
    total_transactions: int
    active_players: int
    total_income: int
    total_expense: int


class EconomicTrendPoint(BaseModel):
    period: str
    trade_count: int
    completed_trades: int
    auction_count: int
    auction_volume: int


class TopTraderItem(BaseModel):
    player_id: str
    trade_count: int


class ReviewEfficiencyMetrics(BaseModel):
    """WP3 ops 看板三字段：审核效率派生指标（来自 review 服务 /stats 端点）。"""

    auto_pass_rate: float | None = None
    manual_intervention_rate: float | None = None
    review_p95_minutes: float | None = None


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
    economy: EconomicOverview | None = None
    review_efficiency: ReviewEfficiencyMetrics | None = None


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


class PlayerMetricItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metric_id: uuid.UUID
    player_id: str
    stat_date: datetime
    total_session_seconds: int = 0
    regions_visited: int = 0
    quests_completed: int = 0
    votes_submitted: int = 0
    npcs_interacted: int = 0
    events_count: int = 0
    detail_jsonb: dict[str, object] | None = None


class RegionMetricItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metric_id: uuid.UUID
    region_id: str
    stat_date: datetime
    unique_players: int = 0
    total_visits: int = 0
    total_duration_seconds: int = 0
    quests_started: int = 0
    quests_completed: int = 0
    events_count: int = 0
    detail_jsonb: dict[str, object] | None = None


class QuestMetricItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metric_id: uuid.UUID
    quest_id: str
    stat_date: datetime
    started_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    avg_duration_seconds: int = 0
    events_count: int = 0
    detail_jsonb: dict[str, object] | None = None


class VoteMetricItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metric_id: uuid.UUID
    vote_cycle_id: str
    stat_date: datetime
    total_votes: int = 0
    unique_voters: int = 0
    candidate_votes_jsonb: dict[str, object] | None = None
    events_count: int = 0
    detail_jsonb: dict[str, object] | None = None


class TrendDataPoint(BaseModel):
    date: str
    value: float


class TrendResponse(BaseModel):
    metric_type: str
    time_range: str
    trends: list[TrendDataPoint]


class AnalyticsReportItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_id: uuid.UUID
    report_type: str
    period_start: datetime
    period_end: datetime
    status: str
    summary_jsonb: dict[str, object] | None = None
    detail_jsonb: dict[str, object] | None = None
    generated_by: str
    trace_id: str | None = None
    schema_version: int
    created_at: datetime
    updated_at: datetime


class AnalyticsOverview(BaseModel):
    total_players: int = 0
    active_players_today: int = 0
    total_votes: int = 0
    votes_today: int = 0
    total_quests_completed: int = 0
    quests_completed_today: int = 0
    total_regions_visited: int = 0
    regions_visited_today: int = 0
    avg_session_duration_seconds: int = 0
    report_count: int = 0


class RegionAnalyticsItem(BaseModel):
    region_id: str
    unique_players: int = 0
    total_visits: int = 0
    total_duration_seconds: int = 0
    quests_started: int = 0
    quests_completed: int = 0


class QuestAnalyticsItem(BaseModel):
    quest_id: str
    started_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    completion_rate: float = 0.0
    avg_duration_seconds: int = 0


class VoteAnalyticsItem(BaseModel):
    vote_cycle_id: str
    total_votes: int = 0
    unique_voters: int = 0
    candidate_votes: dict[str, int] | None = None


class ReportType(str, Enum):
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_SUMMARY = "weekly_summary"
    MONTHLY_SUMMARY = "monthly_summary"
    PLAYER_BEHAVIOR = "player_behavior"
    REGION_HEATMAP = "region_heatmap"
    QUEST_PERFORMANCE = "quest_performance"
    VOTE_ANALYSIS = "vote_analysis"
    CUSTOM = "custom"


class ReportStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class InsightCategory(str, Enum):
    CONTENT_PREFERENCE = "content_preference"
    REGION_HEAT = "region_heat"
    VOTE_PREFERENCE = "vote_preference"
    DIFFICULTY_FEEDBACK = "difficulty_feedback"
    CONTENT_GAP = "content_gap"
    PLAYER_BEHAVIOR = "player_behavior"
    SYSTEM_HEALTH = "system_health"


class QualityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InsightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    insight_id: uuid.UUID
    category: str
    summary: str
    confidence: str
    impact: str
    novelty: str
    feasibility: str
    quality_score: float
    source_report_id: uuid.UUID | None = None
    source_data_jsonb: dict[str, object] | None = None
    tags: list[str] | None = None
    discovered_at: datetime
    created_at: datetime


class RequirementStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class RequirementPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TargetScope(str, Enum):
    CONTENT = "content"
    GAMEPLAY = "gameplay"
    SYSTEM = "system"
    WORLD = "world"


class RequirementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    requirement_id: uuid.UUID
    insight_id: uuid.UUID | None = None
    title: str
    description: str
    status: str
    priority: str
    target_scope: str
    estimated_effort: int
    acceptance_criteria_jsonb: dict[str, object] | None = None
    related_content_jsonb: dict[str, object] | None = None
    generated_by: str
    approved_by: str | None = None
    approved_at: datetime | None = None
    trace_id: str | None = None
    schema_version: int
    created_at: datetime
    updated_at: datetime


class EnvelopeResponse(BaseModel, Generic[T]):
    request_id: str
    data: T
    meta: PaginatedMeta | None = None
    trace_id: str | None = None


# ---- 投票管理 Schema ----


class VoteCycleCreateRequest(BaseModel):
    chapter_id: str
    title: str
    description: str | None = None
    started_at: str | None = None
    ended_at: str | None = None


class VoteCycleTransitionRequest(BaseModel):
    pass


class VoteCycleResponse(BaseModel):
    vote_cycle_id: uuid.UUID | None = None
    chapter_id: str | None = None
    title: str | None = None
    status: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    detail: dict | None = None


# ---- 内容管理 Schema ----


class ContentReleaseRequest(BaseModel):
    release_mode: str = "gray"
    gray_scope: dict | None = None


class ContentRollbackRequest(BaseModel):
    reason: str | None = None


class ContentPackageResponse(BaseModel):
    content_package_id: uuid.UUID | None = None
    version: str | None = None
    status: str | None = None
    region_id: str | None = None
    detail: dict | None = None


# ---- 审核工作流 Schema ----


class ReviewApproveRequest(BaseModel):
    notes: str | None = None


class ReviewRejectRequest(BaseModel):
    reason: str


class ReviewObjectResponse(BaseModel):
    object_id: uuid.UUID | None = None
    object_type: str | None = None
    status: str | None = None
    risk_level: str | None = None
    detail: dict | None = None


class ReviewStatsResponse(BaseModel):
    total_pending: int = 0
    total_approved: int = 0
    total_rejected: int = 0
    total_needs_revision: int = 0
    by_risk_level: dict[str, int] | None = None
    review_efficiency: ReviewEfficiencyMetrics | None = None


# ---- 运营事件 Schema ----


class EventType(str, Enum):
    DOUBLE_REWARD = "double_reward"
    LOGIN_BONUS = "login_bonus"
    LIMITED_TIME = "limited_time"
    SALE = "sale"
    CUSTOM = "custom"


class EventStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    ARCHIVED = "archived"


class EventTargetScope(str, Enum):
    ALL = "all"
    REGION = "region"
    PLAYER_LEVEL = "player_level"
    GUILD = "guild"


class EventCreateRequest(BaseModel):
    event_name: str
    event_type: EventType
    start_at: datetime
    end_at: datetime
    target_scope: EventTargetScope = EventTargetScope.ALL
    target_scope_jsonb: dict[str, object] | None = None
    reward_config_jsonb: dict[str, object] | None = None
    multiplier_config_jsonb: dict[str, object] | None = None
    description: str | None = None
    rules_jsonb: dict[str, object] | None = None


class EventUpdateRequest(BaseModel):
    event_name: str | None = None
    event_type: EventType | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    target_scope: TargetScope | None = None
    target_scope_jsonb: dict[str, object] | None = None
    reward_config_jsonb: dict[str, object] | None = None
    multiplier_config_jsonb: dict[str, object] | None = None
    description: str | None = None
    rules_jsonb: dict[str, object] | None = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: uuid.UUID
    event_name: str
    event_type: str
    status: str
    start_at: datetime
    end_at: datetime
    target_scope: str
    target_scope_jsonb: dict[str, object] | None = None
    reward_config_jsonb: dict[str, object] | None = None
    multiplier_config_jsonb: dict[str, object] | None = None
    description: str | None = None
    rules_jsonb: dict[str, object] | None = None
    created_by: str
    schema_version: int
    created_at: datetime
    updated_at: datetime
