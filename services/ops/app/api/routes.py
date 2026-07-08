import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import RequireOpsScope, UserPayload
from app.core.errors import OpsErrorCodes, raise_ops_error
from app.core.metrics import (
    record_dashboard_view,
    record_ops_action,
)
from app.core.insight_extractor import calculate_quality_score, extract_insights_from_report
from app.core.requirement_generator import generate_requirements_from_insight
from app.repositories.audit_repo import (
    ACTION_DASHBOARD_VIEW,
    ACTION_ANALYTICS_QUERY,
    ACTION_OPS_ACTION_QUERY,
    ACTION_SYSTEM_STATUS_QUERY,
    ACTION_INSIGHT_QUERY,
    ACTION_REQUIREMENT_QUERY,
    ACTION_REQUIREMENT_APPROVE,
    RESOURCE_ANALYTICS,
    RESOURCE_DASHBOARD,
    RESOURCE_OPS_ACTION,
    RESOURCE_SYSTEM,
    RESOURCE_INSIGHT,
    RESOURCE_REQUIREMENT,
    AuditRepository,
)
from app.repositories.analytics_repo import AnalyticsRepository
from app.repositories.dashboard_repo import DashboardRepository
from app.repositories.insight_repo import InsightRepository
from app.repositories.ops_action_repo import OpsActionRepository
from app.repositories.requirement_repo import RequirementRepository
from app.schemas.ops import (
    AnalyticsOverview,
    AnalyticsReportItem,
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
    SystemServiceStatus,
    SystemStatusResponse,
    TrendDataPoint,
    TrendResponse,
    VoteAnalyticsItem,
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
            for candidate, votes in m.candidate_votes_jsonb.items():
                vote_map[m.vote_cycle_id].candidate_votes[candidate] = vote_map[m.vote_cycle_id].candidate_votes.get(candidate, 0) + votes

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
