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
from app.repositories.audit_repo import (
    ACTION_DASHBOARD_VIEW,
    ACTION_OPS_ACTION_QUERY,
    ACTION_SYSTEM_STATUS_QUERY,
    RESOURCE_DASHBOARD,
    RESOURCE_OPS_ACTION,
    RESOURCE_SYSTEM,
    AuditRepository,
)
from app.repositories.dashboard_repo import DashboardRepository
from app.repositories.ops_action_repo import OpsActionRepository
from app.schemas.ops import (
    DashboardMetrics,
    DashboardResponse,
    EnvelopeResponse,
    HealthResponse,
    OpsActionResponse,
    PaginatedMeta,
    SystemServiceStatus,
    SystemStatusResponse,
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
