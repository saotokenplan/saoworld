import uuid

import structlog
from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    RequireContentReadScope,
    RequireContentReleaseScope,
    RequireContentRollbackScope,
    UserPayload,
)
from app.core.errors import ContentErrorCodes, raise_content_error
from app.core.event_publisher import event_publisher
from app.core.metrics import (
    record_package_create,
    record_package_release,
    record_package_rollback,
)
from app.repositories.audit_repo import (
    ACTION_PACKAGE_CREATE,
    ACTION_PACKAGE_RELEASE,
    ACTION_PACKAGE_ROLLBACK,
    RESOURCE_CONTENT_PACKAGE,
    AuditRepository,
)
from app.repositories.content_repo import ContentRepository
from app.schemas.content import (
    ContentPackageListResponse,
    ContentPackageResponse,
    CreatePackageRequest,
    CreatePackageResponse,
    EnvelopeResponse,
    ErrorDetail,
    HealthResponse,
    PackageStatus,
    PaginatedMeta,
    ReleasePackageRequest,
    ReleasePackageResponse,
    RollbackPackageRequest,
    RollbackPackageResponse,
)

router = APIRouter()
ops_router = APIRouter()

logger = structlog.get_logger()


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
    "/content/updates",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["content"],
)
async def list_content_updates(
    request: Request,
    chapter_id: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    x_player_id: str | None = Header(default=None, alias="X-Player-Id"),
    current_user: UserPayload = RequireContentReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[ContentPackageListResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_content_updates")

    player_id = x_player_id or current_user.user_id

    repo = ContentRepository(db)
    packages, total = await repo.list_visible_packages(
        chapter_id=chapter_id,
        player_id=player_id,
        limit=limit,
        offset=offset,
    )

    package_responses = [
        ContentPackageResponse(
            content_package_id=p.content_package_id,
            chapter_id=p.chapter_id,
            region_id=p.region_id,
            package_version=p.package_version,
            source_vote_cycle_id=p.source_vote_cycle_id,
            source_request_id=p.source_request_id,
            title=p.title,
            summary=p.summary,
            status=PackageStatus(p.status),
            gray_scope=p.gray_scope_jsonb,
            payload=p.payload_jsonb,
            schema_version=p.schema_version,
            released_at=p.released_at,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in packages
    ]

    return EnvelopeResponse(
        request_id=request_id,
        data=ContentPackageListResponse(packages=package_responses, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/content/packages/{package_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Package not found"},
    },
    tags=["content"],
)
async def get_package_detail(
    package_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireContentReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[ContentPackageResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_content_package_detail")

    repo = ContentRepository(db)
    pkg = await repo.get_package_by_id(package_id)

    if pkg is None:
        raise_content_error(
            ContentErrorCodes.PACKAGE_NOT_FOUND,
            "内容包不存在",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="path",
                    field="package_id",
                    issue="not_found",
                    rejected_value=str(package_id),
                )
            ],
        )

    if pkg.status not in ("gray", "live") and current_user.role.value not in (
        "ops",
        "system",
        "reviewer",
    ):
        raise_content_error(
            ContentErrorCodes.PACKAGE_NOT_FOUND,
            "内容包不存在",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=ContentPackageResponse(
            content_package_id=pkg.content_package_id,
            chapter_id=pkg.chapter_id,
            region_id=pkg.region_id,
            package_version=pkg.package_version,
            source_vote_cycle_id=pkg.source_vote_cycle_id,
            source_request_id=pkg.source_request_id,
            title=pkg.title,
            summary=pkg.summary,
            status=PackageStatus(pkg.status),
            gray_scope=pkg.gray_scope_jsonb,
            payload=pkg.payload_jsonb,
            schema_version=pkg.schema_version,
            released_at=pkg.released_at,
            created_at=pkg.created_at,
            updated_at=pkg.updated_at,
        ),
        trace_id=trace_id,
    )


@ops_router.post(
    "/content-packages",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["ops"],
)
async def create_package(
    body: CreatePackageRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireContentReleaseScope,
) -> EnvelopeResponse[CreatePackageResponse]:
    request_id = _make_request_id("req_ops_content_package")

    repo = ContentRepository(db)
    pkg = await repo.create_package(
        chapter_id=body.chapter_id,
        region_id=body.region_id,
        package_version=body.package_version,
        source_vote_cycle_id=body.source_vote_cycle_id,
        source_request_id=body.source_request_id,
        title=body.title,
        summary=body.summary,
        payload=body.payload,
        schema_version=body.schema_version,
    )

    # 业务指标：内容包创建计数
    record_package_create()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_PACKAGE_CREATE,
        resource_type=RESOURCE_CONTENT_PACKAGE,
        resource_id=pkg.content_package_id,
        request_payload_jsonb=body.model_dump(mode="json"),
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=CreatePackageResponse(
            content_package_id=pkg.content_package_id,
            chapter_id=pkg.chapter_id,
            title=pkg.title,
            status=PackageStatus(pkg.status),
            package_version=pkg.package_version,
            request_id=request_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )


@ops_router.post(
    "/content-packages/{package_id}/release",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Package not found"},
        409: {"description": "Invalid state transition"},
    },
    tags=["ops"],
)
async def release_package(
    package_id: uuid.UUID,
    body: ReleasePackageRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireContentReleaseScope,
) -> EnvelopeResponse[ReleasePackageResponse]:
    request_id = _make_request_id("req_ops_package_release")

    repo = ContentRepository(db)
    pkg = await repo.get_package_by_id(package_id)

    if pkg is None:
        raise_content_error(
            ContentErrorCodes.PACKAGE_NOT_FOUND,
            "内容包不存在",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="path",
                    field="package_id",
                    issue="not_found",
                    rejected_value=str(package_id),
                )
            ],
        )

    try:
        from_status = pkg.status
        updated_pkg = await repo.release_package(
            package_id=package_id,
            release_mode=body.release_mode.value,
            operator_id=current_user.user_id,
            reason=body.reason,
            trace_id=x_trace_id or _make_request_id("trace"),
            gray_scope=body.gray_scope,
        )
    except ValueError as e:
        if str(e) == "INVALID_PACKAGE_STATE":
            raise_content_error(
                ContentErrorCodes.INVALID_PACKAGE_STATE,
                f"内容包状态 {pkg.status} 不允许当前发布操作",
                request_id=request_id,
                status_code=status.HTTP_409_CONFLICT,
                details=[
                    ErrorDetail(
                        location="body",
                        field="release_mode",
                        issue="invalid_transition",
                        rejected_value=body.release_mode.value,
                    )
                ],
            )
        raise

    # 业务指标：内容包发布计数
    record_package_release(body.release_mode.value)

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_PACKAGE_RELEASE,
        resource_type=RESOURCE_CONTENT_PACKAGE,
        resource_id=package_id,
        reason=body.reason,
        request_payload_jsonb={
            "from_status": from_status,
            "to_status": updated_pkg.status,
            "release_mode": body.release_mode.value,
        },
        result_status=200,
    )

    # 事件发布：内容包发布
    try:
        await event_publisher.publish_content_package_released(
            content_package_id=str(updated_pkg.content_package_id),
            release_mode=body.release_mode.value,
            gray_scope=body.gray_scope or {},
            released_at=updated_pkg.released_at.isoformat() if updated_pkg.released_at else "",
            trace_id=x_trace_id or "",
        )
    except Exception as exc:
        logger.error("event_publish_failed", event_type="content_package_released", content_package_id=str(updated_pkg.content_package_id), error=str(exc))

    return EnvelopeResponse(
        request_id=request_id,
        data=ReleasePackageResponse(
            content_package_id=updated_pkg.content_package_id,
            status=PackageStatus(updated_pkg.status),
            release_mode=body.release_mode,
            request_id=request_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )


@ops_router.post(
    "/content-packages/{package_id}/rollback",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Package not found"},
        409: {"description": "Invalid state transition"},
    },
    tags=["ops"],
)
async def rollback_package(
    package_id: uuid.UUID,
    body: RollbackPackageRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireContentRollbackScope,
) -> EnvelopeResponse[RollbackPackageResponse]:
    request_id = _make_request_id("req_ops_package_rollback")

    repo = ContentRepository(db)
    pkg = await repo.get_package_by_id(package_id)

    if pkg is None:
        raise_content_error(
            ContentErrorCodes.PACKAGE_NOT_FOUND,
            "内容包不存在",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="path",
                    field="package_id",
                    issue="not_found",
                    rejected_value=str(package_id),
                )
            ],
        )

    try:
        from_status = pkg.status
        updated_pkg = await repo.rollback_package(
            package_id=package_id,
            target_version=body.target_version,
            reason=body.reason,
            operator_id=current_user.user_id,
            trace_id=x_trace_id or _make_request_id("trace"),
        )
    except ValueError as e:
        if str(e) == "INVALID_PACKAGE_STATE":
            raise_content_error(
                ContentErrorCodes.INVALID_PACKAGE_STATE,
                f"内容包状态 {pkg.status} 不允许回滚操作",
                request_id=request_id,
                status_code=status.HTTP_409_CONFLICT,
                details=[
                    ErrorDetail(
                        location="body",
                        field="target_version",
                        issue="invalid_transition",
                        rejected_value=body.target_version,
                    )
                ],
            )
        raise

    # 业务指标：内容包回滚计数
    record_package_rollback()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_PACKAGE_ROLLBACK,
        resource_type=RESOURCE_CONTENT_PACKAGE,
        resource_id=package_id,
        reason=body.reason,
        request_payload_jsonb={
            "from_status": from_status,
            "to_status": "rolled_back",
            "target_version": body.target_version,
        },
        result_status=200,
    )

    # 事件发布：内容包回滚
    try:
        from datetime import datetime, timezone
        await event_publisher.publish_content_package_rolled_back(
            content_package_id=str(updated_pkg.content_package_id),
            rollback_reason=body.reason or "",
            rolled_back_at=datetime.now(timezone.utc).isoformat(),
            trace_id=x_trace_id or "",
        )
    except Exception as exc:
        logger.error("event_publish_failed", event_type="content_package_rolled_back", content_package_id=str(updated_pkg.content_package_id), error=str(exc))

    return EnvelopeResponse(
        request_id=request_id,
        data=RollbackPackageResponse(
            content_package_id=updated_pkg.content_package_id,
            status=PackageStatus(updated_pkg.status),
            target_version=body.target_version,
            request_id=request_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )
