import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import RequireOpsRole, RequireWorldReadScope, UserPayload
from app.core.errors import WorldErrorCodes, raise_world_error
from app.core.metrics import (
    record_region_create,
    record_region_status_transition,
)
from app.repositories.audit_repo import (
    ACTION_REGION_CREATE,
    ACTION_REGION_STATUS_UPDATE,
    RESOURCE_REGION,
    AuditRepository,
)
from app.repositories.world_repo import WorldRepository
from app.schemas.world import (
    CreateRegionRequest,
    CreateRegionResponse,
    EnvelopeResponse,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    PaginatedMeta,
    RegionListResponse,
    RegionResponse,
    RegionStatus,
    UpdateRegionStatusRequest,
    UpdateRegionStatusResponse,
)

router = APIRouter()
ops_router = APIRouter()


def _make_request_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


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
    "/world/regions",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["world"],
)
async def list_regions(
    request: Request,
    chapter_id: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireWorldReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[RegionListResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_world_regions")

    repo = WorldRepository(db)
    regions, total = await repo.list_visible_regions(
        chapter_id=chapter_id, limit=limit, offset=offset
    )

    region_responses = [
        RegionResponse(
            region_id=r.region_id,
            chapter_id=r.chapter_id,
            title=r.title,
            summary=r.summary,
            status=RegionStatus(r.status),
            visible=r.visible,
            unlock_condition=r.unlock_condition_jsonb,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in regions
    ]

    return EnvelopeResponse(
        request_id=request_id,
        data=RegionListResponse(regions=region_responses, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/world/regions/{region_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Region not found"},
    },
    tags=["world"],
)
async def get_region_detail(
    region_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireWorldReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[RegionResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_world_region_detail")

    repo = WorldRepository(db)
    region = await repo.get_region_by_id(region_id)

    if region is None:
        raise_world_error(
            WorldErrorCodes.REGION_NOT_FOUND,
            "区域不存在",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="path",
                    field="region_id",
                    issue="not_found",
                    rejected_value=str(region_id),
                )
            ],
        )

    if not region.visible and current_user.role.value not in ("ops", "system", "reviewer"):
        raise_world_error(
            WorldErrorCodes.REGION_NOT_FOUND,
            "区域不存在",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=RegionResponse(
            region_id=region.region_id,
            chapter_id=region.chapter_id,
            title=region.title,
            summary=region.summary,
            status=RegionStatus(region.status),
            visible=region.visible,
            unlock_condition=region.unlock_condition_jsonb,
            created_at=region.created_at,
            updated_at=region.updated_at,
        ),
        trace_id=trace_id,
    )


@ops_router.post(
    "/world/regions",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["ops"],
)
async def create_region(
    body: CreateRegionRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[CreateRegionResponse]:
    request_id = _make_request_id("req_ops_region")

    repo = WorldRepository(db)
    region = await repo.create_region(
        chapter_id=body.chapter_id,
        title=body.title,
        summary=body.summary,
        status=body.status.value,
        visible=body.visible,
        unlock_condition=body.unlock_condition,
    )

    # 业务指标：区域创建计数
    record_region_create()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_REGION_CREATE,
        resource_type=RESOURCE_REGION,
        resource_id=region.region_id,
        request_payload_jsonb=body.model_dump(mode="json"),
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=CreateRegionResponse(
            region_id=region.region_id,
            chapter_id=region.chapter_id,
            title=region.title,
            status=RegionStatus(region.status),
            visible=region.visible,
            request_id=request_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )


@ops_router.post(
    "/world/regions/{region_id}/status",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Region not found"},
        409: {"description": "Invalid status transition"},
    },
    tags=["ops"],
)
async def update_region_status(
    region_id: uuid.UUID,
    body: UpdateRegionStatusRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[UpdateRegionStatusResponse]:
    request_id = _make_request_id("req_ops_region_status")

    repo = WorldRepository(db)
    region = await repo.get_region_by_id(region_id)

    if region is None:
        raise_world_error(
            WorldErrorCodes.REGION_NOT_FOUND,
            "区域不存在",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="path",
                    field="region_id",
                    issue="not_found",
                    rejected_value=str(region_id),
                )
            ],
        )

    if not WorldRepository.is_valid_status_transition(region.status, body.status.value):
        raise_world_error(
            WorldErrorCodes.INVALID_REGION_STATUS,
            f"区域状态 {region.status} 不允许迁移到 {body.status.value}",
            request_id=request_id,
            status_code=status.HTTP_409_CONFLICT,
            details=[
                ErrorDetail(
                    location="body",
                    field="status",
                    issue="invalid_transition",
                    rejected_value=body.status.value,
                )
            ],
        )

    from_status = region.status
    updated_region = await repo.update_region_status(region_id, body.status.value)
    assert updated_region is not None

    # 业务指标：区域状态迁移计数
    record_region_status_transition(from_status, body.status.value)

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_REGION_STATUS_UPDATE,
        resource_type=RESOURCE_REGION,
        resource_id=region_id,
        reason=body.reason,
        request_payload_jsonb={"from_status": from_status, "to_status": body.status.value},
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=UpdateRegionStatusResponse(
            region_id=updated_region.region_id,
            status=RegionStatus(updated_region.status),
            request_id=request_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )
