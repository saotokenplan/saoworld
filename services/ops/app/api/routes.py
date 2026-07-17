import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import RequireOpsScope, UserPayload, require_scope
from app.schemas.auth import Scope
from app.core.errors import OpsErrorCodes, raise_ops_error
from app.core.metrics import (
    record_dashboard_view,
    record_ops_action,
    record_vote_cycle_op,
    record_content_op,
    record_review_op,
    record_event_created,
    record_event_trigger,
    set_active_events_count,
)
from app.core.requirement_generator import generate_requirements_from_insight
from app.core.vote_service_client import VoteServiceClient
from app.core.content_service_client import ContentServiceClient
from app.core.review_service_client import ReviewServiceClient
from app.repositories.audit_repo import (
    ACTION_DASHBOARD_VIEW,
    ACTION_ANALYTICS_QUERY,
    ACTION_OPS_ACTION_QUERY,
    ACTION_SYSTEM_STATUS_QUERY,
    ACTION_INSIGHT_QUERY,
    ACTION_REQUIREMENT_QUERY,
    ACTION_REQUIREMENT_APPROVE,
    ACTION_VOTE_CYCLE_CREATE,
    ACTION_VOTE_CYCLE_SCHEDULE,
    ACTION_VOTE_CYCLE_OPEN,
    ACTION_VOTE_CYCLE_CLOSE,
    ACTION_VOTE_CYCLE_FINALIZE,
    ACTION_CONTENT_RELEASE,
    ACTION_CONTENT_ROLLBACK,
    ACTION_REVIEW_APPROVE,
    ACTION_REVIEW_REJECT,
    ACTION_EVENT_CREATE,
    ACTION_EVENT_UPDATE,
    ACTION_EVENT_ACTIVATE,
    ACTION_EVENT_PAUSE,
    ACTION_EVENT_END,
    ACTION_EVENT_DELETE,
    ACTION_EVENT_QUERY,
    RESOURCE_ANALYTICS,
    RESOURCE_DASHBOARD,
    RESOURCE_OPS_ACTION,
    RESOURCE_SYSTEM,
    RESOURCE_INSIGHT,
    RESOURCE_REQUIREMENT,
    RESOURCE_VOTE_CYCLE,
    RESOURCE_CONTENT_PACKAGE,
    RESOURCE_REVIEW_OBJECT,
    RESOURCE_OPS_EVENT,
    AuditRepository,
)
from app.repositories.analytics_repo import AnalyticsRepository
from app.repositories.dashboard_repo import DashboardRepository
from app.repositories.insight_repo import InsightRepository
from app.repositories.ops_action_repo import OpsActionRepository
from app.repositories.requirement_repo import RequirementRepository
from app.repositories.event_repo import EventRepository
from app.repositories.feedback_repo import FeedbackRepository
from app.schemas.ops import (
    AnalyticsOverview,
    AnalyticsReportItem,
    ContentPackageResponse,
    ContentReleaseRequest,
    ContentRollbackRequest,
    DashboardMetrics,
    DashboardResponse,
    EnvelopeResponse,
    HealthResponse,
    InsightResponse,
    OpsActionResponse,
    PaginatedMeta,
    PlayerMetricItem,
    QuestAnalyticsItem,
    RegionAnalyticsItem,
    RegionMetricItem,
    RequirementResponse,
    ReviewApproveRequest,
    ReviewObjectResponse,
    ReviewRejectRequest,
    ReviewStatsResponse,
    SystemServiceStatus,
    SystemStatusResponse,
    TrendDataPoint,
    TrendResponse,
    VoteAnalyticsItem,
    VoteCycleCreateRequest,
    VoteCycleResponse,
    EventCreateRequest,
    EventUpdateRequest,
    EventResponse,
    EconomicOverview,
    TradeStatsItem,
    EconomicTrendPoint,
)
from app.schemas.feedback import (
    FeedbackSubmit,
    FeedbackUpdate,
    FeedbackResponse,
    FeedbackListResponse,
    FeedbackStatsResponse,
)

router = APIRouter()


def _make_request_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _get_request_id(request: Request) -> str:
    from app.core.config import settings

    return request.headers.get(settings.request_id_header, _make_request_id("req"))


def _get_trace_id(request: Request) -> str | None:
    return request.headers.get("X-Trace-Id")


@router.get("/health", tags=["health"])
async def health_check() -> EnvelopeResponse[HealthResponse]:
    from app.core.config import settings

    return EnvelopeResponse(
        request_id=_make_request_id("req_health"),
        data=HealthResponse(
            service=settings.app_name,
            version=settings.app_version,
        ),
    )


@router.get(
    "/ops/dashboard",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["ops"],
)
async def get_dashboard(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[DashboardResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = DashboardRepository(db)
    dashboard = await repo.get_latest_dashboard()

    if dashboard is None:
        metrics = DashboardMetrics()
        dashboard = await repo.create_dashboard(metrics.model_dump())

    metrics = DashboardMetrics(**dashboard.metrics_jsonb)
    response_data = DashboardResponse(
        dashboard_id=dashboard.dashboard_id,
        metrics=metrics,
        generated_at=dashboard.generated_at,
    )

    record_dashboard_view()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_DASHBOARD_VIEW,
        resource_type=RESOURCE_DASHBOARD,
        resource_id=dashboard.dashboard_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.get(
    "/ops/dashboard/history",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["ops"],
)
async def get_dashboard_history(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[DashboardResponse]]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = DashboardRepository(db)
    dashboards, total = await repo.get_dashboard_history(limit=limit, offset=offset)

    response_data = []
    for d in dashboards:
        metrics = DashboardMetrics(**d.metrics_jsonb)
        response_data.append(DashboardResponse(
            dashboard_id=d.dashboard_id,
            metrics=metrics,
            generated_at=d.generated_at,
        ))

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/ops/actions",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["ops"],
)
async def get_ops_actions(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    action_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    operator_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[OpsActionResponse]]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = OpsActionRepository(db)
    actions, total = await repo.get_actions(
        action_type=action_type,
        status=status,
        operator_id=operator_id,
        limit=limit,
        offset=offset,
    )

    response_data = [OpsActionResponse.model_validate(a) for a in actions]

    record_ops_action("action_query")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_OPS_ACTION_QUERY,
        resource_type=RESOURCE_OPS_ACTION,
        request_payload_jsonb={
            "action_type": action_type,
            "status": status,
            "operator_id": operator_id,
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/ops/actions/{action_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Action not found"},
    },
    tags=["ops"],
)
async def get_ops_action_detail(
    action_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[OpsActionResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = OpsActionRepository(db)
    action = await repo.get_action_by_id(action_id)

    if action is None:
        raise_ops_error(
            OpsErrorCodes.ACTION_NOT_FOUND,
            "运营操作记录不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    response_data = OpsActionResponse.model_validate(action)

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.get(
    "/ops/system/status",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["ops"],
)
async def get_system_status(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[SystemStatusResponse]:
    from app.core.health_check_client import check_all_services_health

    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    health_results = await check_all_services_health()

    services = [
        SystemServiceStatus(name=name, status=status, version=version)
        for name, (status, version) in health_results.items()
    ]

    response_data = SystemStatusResponse(
        services=services,
        timestamp=datetime.now(timezone.utc),
    )

    record_ops_action("system_status")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_SYSTEM_STATUS_QUERY,
        resource_type=RESOURCE_SYSTEM,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.get(
    "/ops/analytics/player-metrics",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["analytics"],
)
async def get_player_metrics(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    player_id: str = Query(...),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[PlayerMetricItem]]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = AnalyticsRepository(db)
    metrics, total = await repo.get_player_metrics(
        player_id=player_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    response_data = [PlayerMetricItem.model_validate(m) for m in metrics]

    record_ops_action("analytics_query")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_ANALYTICS_QUERY,
        resource_type=RESOURCE_ANALYTICS,
        request_payload_jsonb={
            "metric_type": "player",
            "player_id": player_id,
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/ops/analytics/region-metrics",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["analytics"],
)
async def get_region_metrics(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    region_id: str | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[RegionMetricItem]]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = AnalyticsRepository(db)
    metrics, total = await repo.get_region_metrics(
        region_id=region_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    response_data = [RegionMetricItem.model_validate(m) for m in metrics]

    record_ops_action("analytics_query")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_ANALYTICS_QUERY,
        resource_type=RESOURCE_ANALYTICS,
        request_payload_jsonb={
            "metric_type": "region",
            "region_id": region_id,
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/ops/analytics/trends",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["analytics"],
)
async def get_trends(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    metric_type: str = Query(..., pattern="^(region_visits|quest_completion|vote_preference|player_activity)$"),
    time_range: str = Query(default="7d", pattern="^(7d|30d|90d)$"),
    region_id: str | None = Query(default=None),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[TrendResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = AnalyticsRepository(db)
    days = int(time_range.replace("d", ""))
    trend_points: list[TrendDataPoint] = []

    if metric_type == "region_visits":
        metrics, _ = await repo.get_region_metrics(
            region_id=region_id,
            limit=days,
        )
        for m in metrics:
            trend_points.append(TrendDataPoint(
                date=m.stat_date.strftime("%Y-%m-%d"),
                value=float(m.total_visits),
            ))

    trend_points.reverse()

    response_data = TrendResponse(
        metric_type=metric_type,
        time_range=time_range,
        trends=trend_points,
    )

    record_ops_action("analytics_query")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_ANALYTICS_QUERY,
        resource_type=RESOURCE_ANALYTICS,
        request_payload_jsonb={
            "metric_type": metric_type,
            "time_range": time_range,
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.get(
    "/ops/analytics/reports",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["analytics"],
)
async def get_analytics_reports(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    report_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[AnalyticsReportItem]]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = AnalyticsRepository(db)
    reports, total = await repo.get_reports(
        report_type=report_type,
        status=status,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    response_data = [AnalyticsReportItem.model_validate(r) for r in reports]

    record_ops_action("analytics_query")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_ANALYTICS_QUERY,
        resource_type=RESOURCE_ANALYTICS,
        request_payload_jsonb={
            "report_type": report_type,
            "status": status,
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/ops/analytics/dashboard/overview",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["analytics"],
)
async def get_analytics_overview(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[AnalyticsOverview]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = AnalyticsRepository(db)

    player_metrics, _ = await repo.get_player_metrics(player_id="", limit=1000)
    region_metrics, _ = await repo.get_region_metrics(limit=1000)
    quest_metrics, _ = await repo.get_quest_metrics(limit=1000)
    vote_metrics, _ = await repo.get_vote_metrics(limit=1000)
    reports, report_count = await repo.get_reports(limit=1)

    today = datetime.now(timezone.utc).date()

    total_players = len({m.player_id for m in player_metrics})
    active_players_today = len({m.player_id for m in player_metrics if m.stat_date.date() == today})
    total_votes = sum(m.votes_submitted for m in player_metrics)
    votes_today = sum(m.votes_submitted for m in player_metrics if m.stat_date.date() == today)
    total_quests_completed = sum(m.quests_completed for m in player_metrics)
    quests_completed_today = sum(m.quests_completed for m in player_metrics if m.stat_date.date() == today)
    total_regions_visited = sum(m.regions_visited for m in player_metrics)
    regions_visited_today = sum(m.regions_visited for m in player_metrics if m.stat_date.date() == today)

    session_durations = [m.total_session_seconds for m in player_metrics if m.total_session_seconds > 0]
    avg_session_duration_seconds = int(sum(session_durations) / len(session_durations)) if session_durations else 0

    response_data = AnalyticsOverview(
        total_players=total_players,
        active_players_today=active_players_today,
        total_votes=total_votes,
        votes_today=votes_today,
        total_quests_completed=total_quests_completed,
        quests_completed_today=quests_completed_today,
        total_regions_visited=total_regions_visited,
        regions_visited_today=regions_visited_today,
        avg_session_duration_seconds=avg_session_duration_seconds,
        report_count=report_count,
    )

    record_ops_action("analytics_query")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_ANALYTICS_QUERY,
        resource_type=RESOURCE_ANALYTICS,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.get(
    "/ops/analytics/dashboard/regions",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["analytics"],
)
async def get_region_analytics(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[RegionAnalyticsItem]]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = AnalyticsRepository(db)
    metrics, total = await repo.get_region_metrics(limit=limit, offset=offset)

    region_map: dict[str, RegionAnalyticsItem] = {}
    for m in metrics:
        if m.region_id not in region_map:
            region_map[m.region_id] = RegionAnalyticsItem(region_id=m.region_id)
        region_map[m.region_id].unique_players += m.unique_players
        region_map[m.region_id].total_visits += m.total_visits
        region_map[m.region_id].total_duration_seconds += m.total_duration_seconds
        region_map[m.region_id].quests_started += m.quests_started
        region_map[m.region_id].quests_completed += m.quests_completed

    response_data = list(region_map.values())

    record_ops_action("analytics_query")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_ANALYTICS_QUERY,
        resource_type=RESOURCE_ANALYTICS,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/ops/analytics/dashboard/quests",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["analytics"],
)
async def get_quest_analytics(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[QuestAnalyticsItem]]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = AnalyticsRepository(db)
    metrics, total = await repo.get_quest_metrics(limit=limit, offset=offset)

    quest_map: dict[str, QuestAnalyticsItem] = {}
    for m in metrics:
        if m.quest_id not in quest_map:
            quest_map[m.quest_id] = QuestAnalyticsItem(quest_id=m.quest_id)
        quest_map[m.quest_id].started_count += m.started_count
        quest_map[m.quest_id].completed_count += m.completed_count
        quest_map[m.quest_id].failed_count += m.failed_count
        quest_map[m.quest_id].avg_duration_seconds = m.avg_duration_seconds

    for quest in quest_map.values():
        total_started = quest.started_count + quest.failed_count
        quest.completion_rate = round(quest.completed_count / total_started, 2) if total_started > 0 else 0.0

    response_data = list(quest_map.values())

    record_ops_action("analytics_query")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_ANALYTICS_QUERY,
        resource_type=RESOURCE_ANALYTICS,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/ops/analytics/dashboard/votes",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["analytics"],
)
async def get_vote_analytics(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[VoteAnalyticsItem]]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = AnalyticsRepository(db)
    metrics, total = await repo.get_vote_metrics(limit=limit, offset=offset)

    vote_map: dict[str, VoteAnalyticsItem] = {}
    for m in metrics:
        if m.vote_cycle_id not in vote_map:
            vote_map[m.vote_cycle_id] = VoteAnalyticsItem(vote_cycle_id=m.vote_cycle_id)
        vote_map[m.vote_cycle_id].total_votes += m.total_votes
        vote_map[m.vote_cycle_id].unique_voters += m.unique_voters
        if m.candidate_votes_jsonb:
            if vote_map[m.vote_cycle_id].candidate_votes is None:
                vote_map[m.vote_cycle_id].candidate_votes = {}
            cv = vote_map[m.vote_cycle_id].candidate_votes
            assert cv is not None
            for candidate, votes in m.candidate_votes_jsonb.items():
                cv[candidate] = cv.get(candidate, 0) + votes

    response_data = list(vote_map.values())

    record_ops_action("analytics_query")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_ANALYTICS_QUERY,
        resource_type=RESOURCE_ANALYTICS,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/insights",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["insights"],
)
async def get_insights(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    category: str | None = Query(default=None),
    min_confidence: str | None = Query(default=None, pattern="^(low|medium|high)$"),
    min_impact: str | None = Query(default=None, pattern="^(low|medium|high)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[InsightResponse]]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = InsightRepository(db)
    insights, total = await repo.get_insights(
        category=category,
        min_confidence=min_confidence,
        min_impact=min_impact,
        limit=limit,
        offset=offset,
    )

    response_data = [InsightResponse.model_validate(i) for i in insights]

    record_ops_action("insight_query")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_INSIGHT_QUERY,
        resource_type=RESOURCE_INSIGHT,
        request_payload_jsonb={
            "category": category,
            "min_confidence": min_confidence,
            "min_impact": min_impact,
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/insights/{insight_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Insight not found"},
    },
    tags=["insights"],
)
async def get_insight_detail(
    insight_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[InsightResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = InsightRepository(db)
    insight = await repo.get_insight_by_id(insight_id)

    if insight is None:
        raise_ops_error(
            OpsErrorCodes.INSIGHT_NOT_FOUND,
            "洞察记录不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    response_data = InsightResponse.model_validate(insight)

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.post(
    "/ops/insights/{insight_id}/generate-requirement",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Insight not found"},
    },
    tags=["requirements"],
)
async def generate_requirement_from_insight(
    insight_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[RequirementResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    insight_repo = InsightRepository(db)
    insight = await insight_repo.get_insight_by_id(insight_id)

    if insight is None:
        raise_ops_error(
            OpsErrorCodes.INSIGHT_NOT_FOUND,
            "洞察记录不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )
    assert insight is not None

    insight_data = {
        "category": insight.category,
        "summary": insight.summary,
        "confidence": insight.confidence,
        "impact": insight.impact,
        "novelty": insight.novelty,
        "feasibility": insight.feasibility,
        "source_data_jsonb": insight.source_data_jsonb,
    }

    requirements = generate_requirements_from_insight(insight_data)

    req_repo = RequirementRepository(db)
    created_req = await req_repo.create_requirement(
        insight_id=insight_id,
        title=requirements[0]["title"],
        description=requirements[0]["description"],
        priority=requirements[0]["priority"],
        target_scope=requirements[0]["target_scope"],
        estimated_effort=requirements[0]["estimated_effort"],
        acceptance_criteria_jsonb=requirements[0].get("acceptance_criteria_jsonb"),
        related_content_jsonb=requirements[0].get("related_content_jsonb"),
        trace_id=trace_id,
    )

    response_data = RequirementResponse.model_validate(created_req)

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_REQUIREMENT_QUERY,
        resource_type=RESOURCE_REQUIREMENT,
        resource_id=created_req.requirement_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.get(
    "/ops/requirements",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["requirements"],
)
async def get_requirements(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    insight_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    target_scope: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[RequirementResponse]]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = RequirementRepository(db)
    requirements, total = await repo.get_requirements(
        insight_id=insight_id,
        status=status,
        priority=priority,
        target_scope=target_scope,
        limit=limit,
        offset=offset,
    )

    response_data = [RequirementResponse.model_validate(r) for r in requirements]

    record_ops_action("requirement_query")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_REQUIREMENT_QUERY,
        resource_type=RESOURCE_REQUIREMENT,
        request_payload_jsonb={
            "insight_id": str(insight_id) if insight_id else None,
            "status": status,
            "priority": priority,
            "target_scope": target_scope,
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/ops/requirements/{requirement_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Requirement not found"},
    },
    tags=["requirements"],
)
async def get_requirement_detail(
    requirement_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[RequirementResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = RequirementRepository(db)
    requirement = await repo.get_requirement_by_id(requirement_id)

    if requirement is None:
        raise_ops_error(
            OpsErrorCodes.REQUIREMENT_NOT_FOUND,
            "需求包记录不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    response_data = RequirementResponse.model_validate(requirement)

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.post(
    "/ops/requirements/{requirement_id}/approve",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Requirement not found"},
    },
    tags=["requirements"],
)
async def approve_requirement(
    requirement_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[RequirementResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = RequirementRepository(db)
    requirement = await repo.approve_requirement(
        requirement_id=requirement_id,
        approved_by=current_user.user_id,
    )

    if requirement is None:
        raise_ops_error(
            OpsErrorCodes.REQUIREMENT_NOT_FOUND,
            "需求包记录不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    response_data = RequirementResponse.model_validate(requirement)

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_REQUIREMENT_APPROVE,
        resource_type=RESOURCE_REQUIREMENT,
        resource_id=requirement_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


# ============================================================
# 投票管理 API
# ============================================================


@router.post(
    "/ops/vote-cycles",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
    tags=["vote-management"],
)
async def create_vote_cycle(
    body: VoteCycleCreateRequest,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[VoteCycleResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    client = VoteServiceClient()
    try:
        result = await client.create_vote_cycle(
            chapter_id=body.chapter_id,
            title=body.title,
            description=body.description,
            started_at=body.started_at,
            ended_at=body.ended_at,
            token=authorization.replace("Bearer ", "") if authorization and authorization.startswith("Bearer ") else None,
            trace_id=trace_id,
        )
    except Exception as exc:
        raise_ops_error(
            OpsErrorCodes.VOTE_CYCLE_CREATE_FAILED,
            f"投票周期创建失败: {exc}",
            request_id,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    cycle_data = result.get("data", result)
    response_data = VoteCycleResponse(detail=cycle_data)

    record_vote_cycle_op("create")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_VOTE_CYCLE_CREATE,
        resource_type=RESOURCE_VOTE_CYCLE,
        request_payload_jsonb=body.model_dump(),
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.post(
    "/ops/vote-cycles/{vote_cycle_id}/schedule",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
    tags=["vote-management"],
)
async def schedule_vote_cycle(
    vote_cycle_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[VoteCycleResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    client = VoteServiceClient()
    try:
        result = await client.schedule_vote_cycle(
            str(vote_cycle_id),
            token=authorization.replace("Bearer ", "") if authorization and authorization.startswith("Bearer ") else None,
            trace_id=trace_id,
        )
    except Exception as exc:
        raise_ops_error(
            OpsErrorCodes.UPSTREAM_SERVICE_ERROR,
            f"投票周期计划失败: {exc}",
            request_id,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    cycle_data = result.get("data", result)
    response_data = VoteCycleResponse(detail=cycle_data)

    record_vote_cycle_op("schedule")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_VOTE_CYCLE_SCHEDULE,
        resource_type=RESOURCE_VOTE_CYCLE,
        resource_id=vote_cycle_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.post(
    "/ops/vote-cycles/{vote_cycle_id}/open",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
    tags=["vote-management"],
)
async def open_vote_cycle(
    vote_cycle_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[VoteCycleResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    client = VoteServiceClient()
    try:
        result = await client.open_vote_cycle(
            str(vote_cycle_id),
            token=authorization.replace("Bearer ", "") if authorization and authorization.startswith("Bearer ") else None,
            trace_id=trace_id,
        )
    except Exception as exc:
        raise_ops_error(
            OpsErrorCodes.UPSTREAM_SERVICE_ERROR,
            f"投票周期开启失败: {exc}",
            request_id,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    cycle_data = result.get("data", result)
    response_data = VoteCycleResponse(detail=cycle_data)

    record_vote_cycle_op("open")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_VOTE_CYCLE_OPEN,
        resource_type=RESOURCE_VOTE_CYCLE,
        resource_id=vote_cycle_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.post(
    "/ops/vote-cycles/{vote_cycle_id}/close",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
    tags=["vote-management"],
)
async def close_vote_cycle(
    vote_cycle_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[VoteCycleResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    client = VoteServiceClient()
    try:
        result = await client.close_vote_cycle(
            str(vote_cycle_id),
            token=authorization.replace("Bearer ", "") if authorization and authorization.startswith("Bearer ") else None,
            trace_id=trace_id,
        )
    except Exception as exc:
        raise_ops_error(
            OpsErrorCodes.UPSTREAM_SERVICE_ERROR,
            f"投票周期关闭失败: {exc}",
            request_id,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    cycle_data = result.get("data", result)
    response_data = VoteCycleResponse(detail=cycle_data)

    record_vote_cycle_op("close")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_VOTE_CYCLE_CLOSE,
        resource_type=RESOURCE_VOTE_CYCLE,
        resource_id=vote_cycle_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.post(
    "/ops/vote-cycles/{vote_cycle_id}/finalize",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
    tags=["vote-management"],
)
async def finalize_vote_cycle(
    vote_cycle_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[VoteCycleResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    client = VoteServiceClient()
    try:
        result = await client.finalize_vote_cycle(
            str(vote_cycle_id),
            token=authorization.replace("Bearer ", "") if authorization and authorization.startswith("Bearer ") else None,
            trace_id=trace_id,
        )
    except Exception as exc:
        raise_ops_error(
            OpsErrorCodes.UPSTREAM_SERVICE_ERROR,
            f"投票周期确认失败: {exc}",
            request_id,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    cycle_data = result.get("data", result)
    response_data = VoteCycleResponse(detail=cycle_data)

    record_vote_cycle_op("finalize")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_VOTE_CYCLE_FINALIZE,
        resource_type=RESOURCE_VOTE_CYCLE,
        resource_id=vote_cycle_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.get(
    "/ops/vote-cycles",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
    tags=["vote-management"],
)
async def list_vote_cycles(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    cycle_status: str | None = Query(default=None, alias="status"),
    chapter_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[VoteCycleResponse]]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    client = VoteServiceClient()
    try:
        result = await client.list_vote_cycles(
            status=cycle_status,
            chapter_id=chapter_id,
            limit=limit,
            offset=offset,
            token=authorization.replace("Bearer ", "") if authorization and authorization.startswith("Bearer ") else None,
            trace_id=trace_id,
        )
    except Exception as exc:
        raise_ops_error(
            OpsErrorCodes.UPSTREAM_SERVICE_ERROR,
            f"投票周期列表查询失败: {exc}",
            request_id,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    data = result.get("data", [])
    if isinstance(data, dict):
        data = [data]
    response_data = [VoteCycleResponse(detail=item) for item in data]
    meta_data = result.get("meta")
    meta = PaginatedMeta(**meta_data) if meta_data else None

    record_vote_cycle_op("list")

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        meta=meta,
        trace_id=trace_id,
    )


@router.get(
    "/ops/vote-cycles/{vote_cycle_id}",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
    tags=["vote-management"],
)
async def get_vote_cycle_detail(
    vote_cycle_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[VoteCycleResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    client = VoteServiceClient()
    try:
        result = await client.get_vote_cycle_detail(
            str(vote_cycle_id),
            token=authorization.replace("Bearer ", "") if authorization and authorization.startswith("Bearer ") else None,
            trace_id=trace_id,
        )
    except Exception as exc:
        raise_ops_error(
            OpsErrorCodes.UPSTREAM_SERVICE_ERROR,
            f"投票周期详情查询失败: {exc}",
            request_id,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    cycle_data = result.get("data", result)
    response_data = VoteCycleResponse(detail=cycle_data)

    record_vote_cycle_op("detail")

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


# ============================================================
# 内容管理 API
# ============================================================


@router.post(
    "/ops/content-packages/{content_package_id}/release",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
    tags=["content-management"],
)
async def release_content_package(
    content_package_id: uuid.UUID,
    body: ContentReleaseRequest,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[ContentPackageResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    client = ContentServiceClient()
    try:
        result = await client.release_content_package(
            str(content_package_id),
            release_mode=body.release_mode,
            gray_scope=body.gray_scope,
            token=authorization.replace("Bearer ", "") if authorization and authorization.startswith("Bearer ") else None,
            trace_id=trace_id,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        raise_ops_error(
            OpsErrorCodes.CONTENT_RELEASE_FAILED,
            f"内容包发布失败: {exc}",
            request_id,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    pkg_data = result.get("data", result)
    response_data = ContentPackageResponse(detail=pkg_data)

    record_content_op("release")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_CONTENT_RELEASE,
        resource_type=RESOURCE_CONTENT_PACKAGE,
        resource_id=content_package_id,
        request_payload_jsonb=body.model_dump(),
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.post(
    "/ops/content-packages/{content_package_id}/rollback",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
    tags=["content-management"],
)
async def rollback_content_package(
    content_package_id: uuid.UUID,
    body: ContentRollbackRequest,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[ContentPackageResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    client = ContentServiceClient()
    try:
        result = await client.rollback_content_package(
            str(content_package_id),
            reason=body.reason,
            token=authorization.replace("Bearer ", "") if authorization and authorization.startswith("Bearer ") else None,
            trace_id=trace_id,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        raise_ops_error(
            OpsErrorCodes.CONTENT_ROLLBACK_FAILED,
            f"内容包回滚失败: {exc}",
            request_id,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    pkg_data = result.get("data", result)
    response_data = ContentPackageResponse(detail=pkg_data)

    record_content_op("rollback")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_CONTENT_ROLLBACK,
        resource_type=RESOURCE_CONTENT_PACKAGE,
        resource_id=content_package_id,
        reason=body.reason,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.get(
    "/ops/content-packages",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
    tags=["content-management"],
)
async def list_content_packages(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    pkg_status: str | None = Query(default=None, alias="status"),
    region_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[ContentPackageResponse]]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    client = ContentServiceClient()
    try:
        result = await client.list_content_packages(
            status=pkg_status,
            region_id=region_id,
            limit=limit,
            offset=offset,
            token=authorization.replace("Bearer ", "") if authorization and authorization.startswith("Bearer ") else None,
            trace_id=trace_id,
        )
    except Exception as exc:
        raise_ops_error(
            OpsErrorCodes.UPSTREAM_SERVICE_ERROR,
            f"内容包列表查询失败: {exc}",
            request_id,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    data = result.get("data", [])
    if isinstance(data, dict):
        data = [data]
    response_data = [ContentPackageResponse(detail=item) for item in data]
    meta_data = result.get("meta")
    meta = PaginatedMeta(**meta_data) if meta_data else None

    record_content_op("list")

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        meta=meta,
        trace_id=trace_id,
    )


@router.get(
    "/ops/content-packages/{content_package_id}",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
    tags=["content-management"],
)
async def get_content_package_detail(
    content_package_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[ContentPackageResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    client = ContentServiceClient()
    try:
        result = await client.get_content_package_detail(
            str(content_package_id),
            token=authorization.replace("Bearer ", "") if authorization and authorization.startswith("Bearer ") else None,
            trace_id=trace_id,
        )
    except Exception as exc:
        raise_ops_error(
            OpsErrorCodes.UPSTREAM_SERVICE_ERROR,
            f"内容包详情查询失败: {exc}",
            request_id,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    pkg_data = result.get("data", result)
    response_data = ContentPackageResponse(detail=pkg_data)

    record_content_op("detail")

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


# ============================================================
# 审核工作流 API
# ============================================================


@router.post(
    "/ops/review/{object_id}/approve",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
    tags=["review-workflow"],
)
async def approve_review_object(
    object_id: uuid.UUID,
    body: ReviewApproveRequest,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[ReviewObjectResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    client = ReviewServiceClient()
    try:
        result = await client.approve_review_object(
            str(object_id),
            notes=body.notes,
            token=authorization.replace("Bearer ", "") if authorization and authorization.startswith("Bearer ") else None,
            trace_id=trace_id,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        raise_ops_error(
            OpsErrorCodes.REVIEW_APPROVE_FAILED,
            f"审核批准失败: {exc}",
            request_id,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    obj_data = result.get("data", result)
    response_data = ReviewObjectResponse(detail=obj_data)

    record_review_op("approve")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_REVIEW_APPROVE,
        resource_type=RESOURCE_REVIEW_OBJECT,
        resource_id=object_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.post(
    "/ops/review/{object_id}/reject",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
    tags=["review-workflow"],
)
async def reject_review_object(
    object_id: uuid.UUID,
    body: ReviewRejectRequest,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[ReviewObjectResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    client = ReviewServiceClient()
    try:
        result = await client.reject_review_object(
            str(object_id),
            reason=body.reason,
            token=authorization.replace("Bearer ", "") if authorization and authorization.startswith("Bearer ") else None,
            trace_id=trace_id,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        raise_ops_error(
            OpsErrorCodes.REVIEW_REJECT_FAILED,
            f"审核拒绝失败: {exc}",
            request_id,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    obj_data = result.get("data", result)
    response_data = ReviewObjectResponse(detail=obj_data)

    record_review_op("reject")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_REVIEW_REJECT,
        resource_type=RESOURCE_REVIEW_OBJECT,
        resource_id=object_id,
        reason=body.reason,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.get(
    "/ops/review/objects",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
    tags=["review-workflow"],
)
async def list_review_objects(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    obj_status: str | None = Query(default=None, alias="status"),
    risk_level: str | None = Query(default=None),
    object_type: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[ReviewObjectResponse]]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    client = ReviewServiceClient()
    try:
        result = await client.list_review_objects(
            status=obj_status,
            risk_level=risk_level,
            object_type=object_type,
            limit=limit,
            offset=offset,
            token=authorization.replace("Bearer ", "") if authorization and authorization.startswith("Bearer ") else None,
            trace_id=trace_id,
        )
    except Exception as exc:
        raise_ops_error(
            OpsErrorCodes.UPSTREAM_SERVICE_ERROR,
            f"审核列表查询失败: {exc}",
            request_id,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    data = result.get("data", [])
    if isinstance(data, dict):
        data = [data]
    response_data = [ReviewObjectResponse(detail=item) for item in data]
    meta_data = result.get("meta")
    meta = PaginatedMeta(**meta_data) if meta_data else None

    record_review_op("list")

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        meta=meta,
        trace_id=trace_id,
    )


@router.get(
    "/ops/review/stats",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
    tags=["review-workflow"],
)
async def get_review_stats(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[ReviewStatsResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    client = ReviewServiceClient()
    try:
        result = await client.get_review_stats(
            token=authorization.replace("Bearer ", "") if authorization and authorization.startswith("Bearer ") else None,
            trace_id=trace_id,
        )
    except Exception as exc:
        raise_ops_error(
            OpsErrorCodes.UPSTREAM_SERVICE_ERROR,
            f"审核统计查询失败: {exc}",
            request_id,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    stats_data = result.get("data", result)
    response_data = ReviewStatsResponse(**stats_data) if isinstance(stats_data, dict) else ReviewStatsResponse()

    record_review_op("stats")

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


# ============================================================
# 运营事件 API
# ============================================================


@router.post(
    "/ops/events",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        409: {"description": "Event name exists or time overlap"},
    },
    tags=["ops-events"],
)
async def create_event(
    body: EventCreateRequest,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[EventResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = EventRepository(db)

    existing = await repo.get_event_by_name(body.event_name)
    if existing is not None:
        raise_ops_error(
            OpsErrorCodes.EVENT_NAME_EXISTS,
            f"事件名称已存在: {body.event_name}",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    from app.core.event_engine import EventEngine
    valid, errors = EventEngine.validate_event_config(body.model_dump())
    if not valid:
        raise_ops_error(
            OpsErrorCodes.INVALID_EVENT_CONFIG,
            f"事件配置无效: {'; '.join(errors)}",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    event = await repo.create_event(
        event_name=body.event_name,
        event_type=body.event_type.value,
        start_at=body.start_at,
        end_at=body.end_at,
        target_scope=body.target_scope.value,
        target_scope_jsonb=body.target_scope_jsonb,
        reward_config_jsonb=body.reward_config_jsonb,
        multiplier_config_jsonb=body.multiplier_config_jsonb,
        description=body.description,
        rules_jsonb=body.rules_jsonb,
        created_by=current_user.user_id,
    )

    response_data = EventResponse.model_validate(event)

    record_event_created(body.event_type.value)

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_EVENT_CREATE,
        resource_type=RESOURCE_OPS_EVENT,
        resource_id=event.event_id,
        request_payload_jsonb=body.model_dump(mode="json"),
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.get(
    "/ops/events",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["ops-events"],
)
async def list_events(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    event_type: str | None = Query(default=None),
    event_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[EventResponse]]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = EventRepository(db)
    events, total = await repo.list_events(
        event_type=event_type,
        status=event_status,
        limit=limit,
        offset=offset,
    )

    response_data = [EventResponse.model_validate(e) for e in events]

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_EVENT_QUERY,
        resource_type=RESOURCE_OPS_EVENT,
        request_payload_jsonb={
            "event_type": event_type,
            "status": event_status,
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/ops/events/active",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["ops-events"],
)
async def get_active_events_ops(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[EventResponse]]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = EventRepository(db)
    events = await repo.get_active_events()

    response_data = [EventResponse.model_validate(e) for e in events]
    set_active_events_count(len(response_data))

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.get(
    "/ops/events/{event_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Event not found"},
    },
    tags=["ops-events"],
)
async def get_event_detail(
    event_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[EventResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = EventRepository(db)
    event = await repo.get_event_by_id(event_id)

    if event is None:
        raise_ops_error(
            OpsErrorCodes.EVENT_NOT_FOUND,
            "运营事件不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    response_data = EventResponse.model_validate(event)

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.put(
    "/ops/events/{event_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Event not found"},
    },
    tags=["ops-events"],
)
async def update_event(
    event_id: uuid.UUID,
    body: EventUpdateRequest,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[EventResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = EventRepository(db)
    event = await repo.get_event_by_id(event_id)

    if event is None:
        raise_ops_error(
            OpsErrorCodes.EVENT_NOT_FOUND,
            "运营事件不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if body.event_name is not None and body.event_name != event.event_name:
        existing = await repo.get_event_by_name(body.event_name)
        if existing is not None:
            raise_ops_error(
                OpsErrorCodes.EVENT_NAME_EXISTS,
                f"事件名称已存在: {body.event_name}",
                request_id,
                status_code=status.HTTP_409_CONFLICT,
            )

    updated = await repo.update_event(
        event_id=event_id,
        event_name=body.event_name,
        event_type=body.event_type.value if body.event_type else None,
        start_at=body.start_at,
        end_at=body.end_at,
        target_scope=body.target_scope.value if body.target_scope else None,
        target_scope_jsonb=body.target_scope_jsonb,
        reward_config_jsonb=body.reward_config_jsonb,
        multiplier_config_jsonb=body.multiplier_config_jsonb,
        description=body.description,
        rules_jsonb=body.rules_jsonb,
    )

    assert updated is not None
    response_data = EventResponse.model_validate(updated)

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_EVENT_UPDATE,
        resource_type=RESOURCE_OPS_EVENT,
        resource_id=event_id,
        request_payload_jsonb=body.model_dump(exclude_unset=True, mode="json"),
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.post(
    "/ops/events/{event_id}/activate",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Event not found"},
        409: {"description": "Invalid status transition"},
    },
    tags=["ops-events"],
)
async def activate_event(
    event_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[EventResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = EventRepository(db)
    event = await repo.get_event_by_id(event_id)

    if event is None:
        raise_ops_error(
            OpsErrorCodes.EVENT_NOT_FOUND,
            "运营事件不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if event.status not in ("draft", "paused"):
        raise_ops_error(
            OpsErrorCodes.INVALID_EVENT_STATUS,
            f"当前状态 {event.status} 不允许激活",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    updated = await repo.update_event_status(event_id, "active")
    assert updated is not None
    response_data = EventResponse.model_validate(updated)

    record_event_trigger(updated.event_type)

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_EVENT_ACTIVATE,
        resource_type=RESOURCE_OPS_EVENT,
        resource_id=event_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.post(
    "/ops/events/{event_id}/pause",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Event not found"},
        409: {"description": "Invalid status transition"},
    },
    tags=["ops-events"],
)
async def pause_event(
    event_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[EventResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = EventRepository(db)
    event = await repo.get_event_by_id(event_id)

    if event is None:
        raise_ops_error(
            OpsErrorCodes.EVENT_NOT_FOUND,
            "运营事件不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if event.status != "active":
        raise_ops_error(
            OpsErrorCodes.INVALID_EVENT_STATUS,
            f"当前状态 {event.status} 不允许暂停",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    updated = await repo.update_event_status(event_id, "paused")
    assert updated is not None
    response_data = EventResponse.model_validate(updated)

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_EVENT_PAUSE,
        resource_type=RESOURCE_OPS_EVENT,
        resource_id=event_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.post(
    "/ops/events/{event_id}/end",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Event not found"},
        409: {"description": "Invalid status transition"},
    },
    tags=["ops-events"],
)
async def end_event(
    event_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[EventResponse]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = EventRepository(db)
    event = await repo.get_event_by_id(event_id)

    if event is None:
        raise_ops_error(
            OpsErrorCodes.EVENT_NOT_FOUND,
            "运营事件不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if event.status not in ("active", "paused"):
        raise_ops_error(
            OpsErrorCodes.INVALID_EVENT_STATUS,
            f"当前状态 {event.status} 不允许结束",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    updated = await repo.update_event_status(event_id, "ended")
    assert updated is not None
    response_data = EventResponse.model_validate(updated)

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_EVENT_END,
        resource_type=RESOURCE_OPS_EVENT,
        resource_id=event_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.delete(
    "/ops/events/{event_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Event not found"},
    },
    tags=["ops-events"],
)
async def delete_event(
    event_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[dict]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = EventRepository(db)
    deleted = await repo.delete_event(event_id)

    if not deleted:
        raise_ops_error(
            OpsErrorCodes.EVENT_NOT_FOUND,
            "运营事件不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_EVENT_DELETE,
        resource_type=RESOURCE_OPS_EVENT,
        resource_id=event_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data={"deleted": True, "event_id": event_id},
        trace_id=trace_id,
    )


# ============================================================
# 玩家侧事件 API
# ============================================================


@router.get(
    "/player/events/active",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["player-events"],
)
async def get_player_active_events(
    request: Request,
    current_user: UserPayload = require_scope(Scope.EVENTS_READ),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[EventResponse]]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = EventRepository(db)
    events = await repo.get_active_events()

    response_data = [EventResponse.model_validate(e) for e in events]

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


# ============================================================
# 用户反馈 API
# ============================================================


ACTION_FEEDBACK_SUBMIT = "feedback_submit"
ACTION_FEEDBOOK_UPDATE = "feedback_update"
ACTION_FEEDBACK_QUERY = "feedback_query"
RESOURCE_FEEDBACK = "feedback"


@router.post(
    "/feedback",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
    tags=["feedback"],
    status_code=status.HTTP_201_CREATED,
)
async def submit_feedback(
    body: FeedbackSubmit,
    request: Request,
    current_user: UserPayload = require_scope(Scope.FEEDBACK_SUBMIT),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    x_player_id: str | None = Header(default=None, alias="X-Player-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[FeedbackResponse]:
    """玩家提交反馈。"""
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")
    player_id = x_player_id or current_user.user_id

    # 校验反馈类型
    valid_types = ("bug", "suggestion", "question", "other")
    if body.feedback_type not in valid_types:
        raise_ops_error(
            OpsErrorCodes.INVALID_FEEDBACK_TYPE,
            f"无效的反馈类型: {body.feedback_type}",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 校验优先级
    valid_priorities = ("low", "medium", "high", "critical")
    if body.priority not in valid_priorities:
        raise_ops_error(
            OpsErrorCodes.INVALID_ARGUMENT,
            f"无效的优先级: {body.priority}",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    repo = FeedbackRepository(db)
    feedback = await repo.create(
        player_id=player_id,
        feedback_type=body.feedback_type,
        title=body.title,
        content=body.content,
        priority=body.priority,
        region_id=body.region_id,
        chapter_id=body.chapter_id,
        attachment_urls=body.attachment_urls,
        metadata_jsonb=body.metadata,
        trace_id=trace_id,
    )

    from app.core.metrics import record_feedback_submitted
    record_feedback_submitted(body.feedback_type)

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=player_id,
        operator_role="player",
        action=ACTION_FEEDBACK_SUBMIT,
        resource_type=RESOURCE_FEEDBACK,
        resource_id=feedback.feedback_id,
        result_status=201,
    )

    await db.commit()

    return EnvelopeResponse(
        request_id=request_id,
        data=FeedbackResponse.model_validate(feedback),
        trace_id=trace_id,
    )


@router.get(
    "/ops/feedback",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
    tags=["feedback"],
)
async def list_feedback(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    status: str | None = Query(default=None),
    feedback_type: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    player_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[FeedbackListResponse]:
    """运营列表查询反馈。"""
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = FeedbackRepository(db)
    feedbacks = await repo.list(
        status=status,
        feedback_type=feedback_type,
        priority=priority,
        player_id=player_id,
        limit=limit,
        offset=offset,
    )
    total = await repo.count(
        status=status,
        feedback_type=feedback_type,
        priority=priority,
        player_id=player_id,
    )

    response_data = FeedbackListResponse(
        feedbacks=[FeedbackResponse.model_validate(f) for f in feedbacks],
        total=total,
        limit=limit,
        offset=offset,
    )

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_FEEDBACK_QUERY,
        resource_type=RESOURCE_FEEDBACK,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.get(
    "/ops/feedback/stats",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
    tags=["feedback"],
)
async def get_feedback_stats(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[FeedbackStatsResponse]:
    """运营查询反馈统计。"""
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = FeedbackRepository(db)

    total = await repo.count()
    pending = await repo.count(status="pending")
    in_progress = await repo.count(status="in_progress")
    resolved = await repo.count(status="resolved")
    closed = await repo.count(status="closed")

    # 按类型统计
    by_type = {}
    for t in ("bug", "suggestion", "question", "other"):
        by_type[t] = await repo.count(feedback_type=t)

    # 按优先级统计
    by_priority = {}
    for p in ("low", "medium", "high", "critical"):
        by_priority[p] = await repo.count(priority=p)

    response_data = FeedbackStatsResponse(
        total=total,
        pending=pending,
        in_progress=in_progress,
        resolved=resolved,
        closed=closed,
        by_type=by_type,
        by_priority=by_priority,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data,
        trace_id=trace_id,
    )


@router.get(
    "/ops/feedback/{feedback_id}",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}, 404: {"description": "Feedback not found"}},
    tags=["feedback"],
)
async def get_feedback(
    feedback_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[FeedbackResponse]:
    """运营查询反馈详情。"""
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = FeedbackRepository(db)
    feedback = await repo.get_by_id(feedback_id)

    if not feedback:
        raise_ops_error(
            OpsErrorCodes.FEEDBACK_NOT_FOUND,
            "反馈不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=FeedbackResponse.model_validate(feedback),
        trace_id=trace_id,
    )


@router.patch(
    "/ops/feedback/{feedback_id}",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}, 404: {"description": "Feedback not found"}},
    tags=["feedback"],
)
async def update_feedback(
    feedback_id: uuid.UUID,
    body: FeedbackUpdate,
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[FeedbackResponse]:
    """运营更新反馈状态。"""
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    repo = FeedbackRepository(db)
    feedback = await repo.get_by_id(feedback_id)

    if not feedback:
        raise_ops_error(
            OpsErrorCodes.FEEDBACK_NOT_FOUND,
            "反馈不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # 校验状态
    if body.status:
        valid_statuses = ("pending", "in_progress", "resolved", "closed")
        if body.status not in valid_statuses:
            raise_ops_error(
                OpsErrorCodes.INVALID_FEEDBACK_STATUS,
                f"无效的状态: {body.status}",
                request_id,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    # 校验优先级
    if body.priority:
        valid_priorities = ("low", "medium", "high", "critical")
        if body.priority not in valid_priorities:
            raise_ops_error(
                OpsErrorCodes.INVALID_ARGUMENT,
                f"无效的优先级: {body.priority}",
                request_id,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    # 更新状态
    if body.status:
        feedback = await repo.update_status(
            feedback_id=feedback_id,
            new_status=body.status,
            resolved_by=current_user.user_id,
            resolution_note=body.resolution_note,
        )
        from app.core.metrics import record_feedback_status
        record_feedback_status(body.status)

    # 更新优先级
    if body.priority:
        feedback = await repo.update_priority(
            feedback_id=feedback_id,
            new_priority=body.priority,
        )

    await db.commit()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_FEEDBOOK_UPDATE,
        resource_type=RESOURCE_FEEDBACK,
        resource_id=feedback_id,
        result_status=200,
    )

    assert feedback is not None
    return EnvelopeResponse(
        request_id=request_id,
        data=FeedbackResponse.model_validate(feedback),
        trace_id=trace_id,
    )


@router.get(
    "/ops/analytics/dashboard/economy/overview",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["analytics"],
)
async def get_economy_overview(
    request: Request,
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[EconomicOverview]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    dashboard_repo = DashboardRepository(db)
    latest_dashboard = await dashboard_repo.get_latest_dashboard()

    economy_data = {}
    if latest_dashboard and latest_dashboard.metrics_jsonb:
        economy_data = latest_dashboard.metrics_jsonb.get("economy", {})

    overview = EconomicOverview(**economy_data)

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_DASHBOARD_VIEW,
        resource_type=RESOURCE_DASHBOARD,
        resource_id=None,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=overview,
        trace_id=trace_id,
    )


@router.get(
    "/ops/analytics/dashboard/economy/trends",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["analytics"],
)
async def get_economy_trends(
    request: Request,
    days: int = Query(default=30, ge=1, le=365),
    granularity: str = Query(default="day"),
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[EconomicTrendPoint]]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    dashboard_repo = DashboardRepository(db)
    latest_dashboard = await dashboard_repo.get_latest_dashboard()

    trends_data = []
    if latest_dashboard and latest_dashboard.metrics_jsonb:
        trends_data = latest_dashboard.metrics_jsonb.get("economy_trends", [])

    trends = [EconomicTrendPoint(**item) for item in trends_data]

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_DASHBOARD_VIEW,
        resource_type=RESOURCE_DASHBOARD,
        resource_id=None,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=trends,
        trace_id=trace_id,
    )


@router.get(
    "/ops/analytics/dashboard/economy/trade-stats",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["analytics"],
)
async def get_economy_trade_stats(
    request: Request,
    days: int = Query(default=7, ge=1, le=365),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireOpsScope,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[TradeStatsItem]]:
    request_id = _get_request_id(request)
    trace_id = x_trace_id or _make_request_id("trace")

    dashboard_repo = DashboardRepository(db)
    latest_dashboard = await dashboard_repo.get_latest_dashboard()

    trade_stats_data = []
    total = 0
    if latest_dashboard and latest_dashboard.metrics_jsonb:
        trade_stats_data = latest_dashboard.metrics_jsonb.get("trade_stats", [])
        total = len(trade_stats_data)

    items = [TradeStatsItem(**item) for item in trade_stats_data]

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_DASHBOARD_VIEW,
        resource_type=RESOURCE_DASHBOARD,
        resource_id=None,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=items,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )
