import uuid

import structlog
from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import RequireOpsRole, RequireReviewApproveScope, UserPayload
from app.core.errors import GenerationErrorCodes, raise_generation_error
from app.core.event_publisher import event_publisher
from app.core.metrics import (
    record_generated_object_status,
    record_generation_request_status,
)
from app.core.quality_scorer import quality_scorer
from app.core.skeleton_validator import skeleton_validator
from app.repositories.audit_repo import (
    ACTION_GENERATED_OBJECT_CREATE,
    ACTION_GENERATED_OBJECT_STATUS_UPDATE,
    ACTION_GENERATION_REQUEST_CREATE,
    ACTION_GENERATION_REQUEST_STATUS_UPDATE,
    RESOURCE_GENERATED_OBJECT,
    RESOURCE_GENERATION_REQUEST,
    AuditRepository,
)
from app.repositories.generation_repo import GenerationRepository
from app.schemas.generation import (
    CreateGenerationRequestRequest,
    CreateGenerationRequestResponse,
    CreateGeneratedObjectRequest,
    CreateGeneratedObjectResponse,
    EnvelopeResponse,
    ErrorDetail,
    GeneratedObjectListResponse,
    GeneratedObjectResponse,
    GeneratedObjectStatus,
    GenerationRequestListResponse,
    GenerationRequestResponse,
    GenerationRequestStatus,
    HealthResponse,
    PaginatedMeta,
    UpdateGenerationStatusRequest,
    UpdateGenerationStatusResponse,
    UpdateObjectStatusRequest,
    UpdateObjectStatusResponse,
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


@ops_router.get(
    "/generation/requests",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["ops"],
)
async def list_generation_requests(
    request: Request,
    status_filter: GenerationRequestStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireOpsRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GenerationRequestListResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_gen_requests_list")

    repo = GenerationRepository(db)
    requests_list, total = await repo.list_requests(
        status=status_filter.value if status_filter else None,
        limit=limit,
        offset=offset,
    )

    request_responses = [
        GenerationRequestResponse(
            request_id=req.request_id,
            vote_cycle_id=req.vote_cycle_id,
            source_candidate_id=req.source_candidate_id,
            template_id=req.template_id,
            input_payload=req.input_payload_jsonb,
            status=GenerationRequestStatus(req.status),
            retry_count=req.retry_count,
            max_retries=req.max_retries,
            error_message=req.error_message,
            trace_id=req.trace_id,
            created_at=req.created_at,
            updated_at=req.updated_at,
        )
        for req in requests_list
    ]

    return EnvelopeResponse(
        request_id=request_id,
        data=GenerationRequestListResponse(requests=request_responses, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@ops_router.get(
    "/generation/requests/{request_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Request not found"},
    },
    tags=["ops"],
)
async def get_generation_request_detail(
    request_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireOpsRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GenerationRequestResponse]:
    trace_id = _get_trace_id(request)
    req_id = _make_request_id("req_gen_request_detail")

    repo = GenerationRepository(db)
    req = await repo.get_request_by_id(request_id)

    if req is None:
        raise_generation_error(
            GenerationErrorCodes.REQUEST_NOT_FOUND,
            "生成请求不存在",
            req_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="path",
                    field="request_id",
                    issue="not_found",
                    rejected_value=str(request_id),
                )
            ],
        )

    return EnvelopeResponse(
        request_id=req_id,
        data=GenerationRequestResponse(
            request_id=req.request_id,
            vote_cycle_id=req.vote_cycle_id,
            source_candidate_id=req.source_candidate_id,
            template_id=req.template_id,
            input_payload=req.input_payload_jsonb,
            status=GenerationRequestStatus(req.status),
            retry_count=req.retry_count,
            max_retries=req.max_retries,
            error_message=req.error_message,
            trace_id=req.trace_id,
            created_at=req.created_at,
            updated_at=req.updated_at,
        ),
        trace_id=trace_id,
    )


@ops_router.post(
    "/generation/requests",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "World skeleton not found"},
    },
    tags=["ops"],
)
async def create_generation_request(
    body: CreateGenerationRequestRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[CreateGenerationRequestResponse]:
    request_id = _make_request_id("req_ops_gen_request")

    await skeleton_validator.validate_generation_request(body.input_payload, request_id)

    repo = GenerationRepository(db)
    req = await repo.create_request(
        template_id=body.template_id,
        input_payload=body.input_payload,
        trace_id=body.trace_id,
        vote_cycle_id=body.vote_cycle_id,
        source_candidate_id=body.source_candidate_id,
    )

    record_generation_request_status(req.status)

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_GENERATION_REQUEST_CREATE,
        resource_type=RESOURCE_GENERATION_REQUEST,
        resource_id=req.request_id,
        request_payload_jsonb=body.model_dump(mode="json"),
        result_status=201,
    )

    # 事件发布：生成请求创建
    try:
        target_type = body.input_payload.get("target_type", "npc")
        region_id = body.input_payload.get("region_id", "")
        await event_publisher.publish_generation_request_created(
            request_id=str(req.request_id),
            vote_cycle_id=str(body.vote_cycle_id) if body.vote_cycle_id else "",
            target_type=str(target_type),
            region_id=str(region_id),
            created_at=req.created_at.isoformat() if req.created_at else "",
            trace_id=x_trace_id or "",
        )
    except Exception as exc:
        logger.error("event_publish_failed", event_type="generation_request_created", request_id=str(req.request_id), error=str(exc))

    return EnvelopeResponse(
        request_id=request_id,
        data=CreateGenerationRequestResponse(
            request_id=req.request_id,
            template_id=req.template_id,
            status=GenerationRequestStatus(req.status),
            request_id_=request_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )


@ops_router.post(
    "/generation/requests/{request_id}/status",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Request not found"},
        409: {"description": "Invalid state transition"},
    },
    tags=["ops"],
)
async def update_generation_request_status(
    request_id: uuid.UUID,
    body: UpdateGenerationStatusRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[UpdateGenerationStatusResponse]:
    req_id = _make_request_id("req_ops_gen_status")

    repo = GenerationRepository(db)
    req = await repo.get_request_by_id(request_id)

    if req is None:
        raise_generation_error(
            GenerationErrorCodes.REQUEST_NOT_FOUND,
            "生成请求不存在",
            req_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="path",
                    field="request_id",
                    issue="not_found",
                    rejected_value=str(request_id),
                )
            ],
        )

    try:
        from_status = req.status
        updated_req = await repo.update_request_status(
            request_id=request_id,
            new_status=body.status.value,
            error_message=body.error_message,
        )
    except ValueError as e:
        if str(e) == "INVALID_REQUEST_STATUS":
            raise_generation_error(
                GenerationErrorCodes.INVALID_REQUEST_STATUS,
                f"生成请求状态 {req.status} 不允许当前操作",
                req_id,
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
        if str(e) == "MAX_RETRIES_EXCEEDED":
            raise_generation_error(
                GenerationErrorCodes.MAX_RETRIES_EXCEEDED,
                "已达到最大重试次数",
                req_id,
                status_code=status.HTTP_409_CONFLICT,
                details=[
                    ErrorDetail(
                        location="body",
                        field="status",
                        issue="max_retries_exceeded",
                        rejected_value=body.status.value,
                    )
                ],
            )
        raise

    record_generation_request_status(updated_req.status)

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_GENERATION_REQUEST_STATUS_UPDATE,
        resource_type=RESOURCE_GENERATION_REQUEST,
        resource_id=request_id,
        request_payload_jsonb={
            "from_status": from_status,
            "to_status": updated_req.status,
            "error_message": body.error_message,
        },
        result_status=200,
    )

    # 事件发布：批量生成完成（当状态变为 succeeded 时）
    if updated_req.status == "succeeded":
        try:
            from datetime import datetime, timezone
            objects = await repo.list_objects_by_request_id(request_id=request_id)
            generated_objects = [
                {
                    "object_id": str(obj.object_id),
                    "object_type": obj.object_type,
                    "status": obj.status,
                }
                for obj in objects
            ]
            await event_publisher.publish_generation_batch_completed(
                request_id=str(request_id),
                generated_objects=generated_objects,
                completed_at=datetime.now(timezone.utc).isoformat(),
                status="succeeded",
                trace_id=x_trace_id or "",
            )
        except Exception as exc:
            logger.error("event_publish_failed", event_type="generation_batch_completed", request_id=str(request_id), error=str(exc))

    return EnvelopeResponse(
        request_id=req_id,
        data=UpdateGenerationStatusResponse(
            request_id=updated_req.request_id,
            status=GenerationRequestStatus(updated_req.status),
            request_id_=req_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )


@ops_router.get(
    "/generation/objects",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["ops"],
)
async def list_generated_objects(
    request: Request,
    status_filter: GeneratedObjectStatus | None = Query(default=None, alias="status"),
    object_type: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireOpsRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GeneratedObjectListResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_gen_objects_list")

    repo = GenerationRepository(db)
    objects, total = await repo.list_objects(
        status=status_filter.value if status_filter else None,
        object_type=object_type,
        limit=limit,
        offset=offset,
    )

    object_responses = [
        GeneratedObjectResponse(
            object_id=obj.object_id,
            request_id=obj.request_id,
            object_type=obj.object_type,
            schema_version=obj.schema_version,
            object_payload=obj.object_payload_jsonb,
            quality_score=obj.quality_score,
            status=GeneratedObjectStatus(obj.status),
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )
        for obj in objects
    ]

    return EnvelopeResponse(
        request_id=request_id,
        data=GeneratedObjectListResponse(objects=object_responses, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@ops_router.get(
    "/generation/objects/{object_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Object not found"},
    },
    tags=["ops"],
)
async def get_generated_object_detail(
    object_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireOpsRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GeneratedObjectResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_gen_object_detail")

    repo = GenerationRepository(db)
    obj = await repo.get_object_by_id(object_id)

    if obj is None:
        raise_generation_error(
            GenerationErrorCodes.OBJECT_NOT_FOUND,
            "生成对象不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="path",
                    field="object_id",
                    issue="not_found",
                    rejected_value=str(object_id),
                )
            ],
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=GeneratedObjectResponse(
            object_id=obj.object_id,
            request_id=obj.request_id,
            object_type=obj.object_type,
            schema_version=obj.schema_version,
            object_payload=obj.object_payload_jsonb,
            quality_score=obj.quality_score,
            status=GeneratedObjectStatus(obj.status),
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        ),
        trace_id=trace_id,
    )


@ops_router.post(
    "/generation/objects/{object_id}/status",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Object not found"},
        409: {"description": "Invalid state transition"},
    },
    tags=["ops"],
)
async def update_generated_object_status(
    object_id: uuid.UUID,
    body: UpdateObjectStatusRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireReviewApproveScope,
) -> EnvelopeResponse[UpdateObjectStatusResponse]:
    request_id = _make_request_id("req_ops_object_status")

    repo = GenerationRepository(db)
    obj = await repo.get_object_by_id(object_id)

    if obj is None:
        raise_generation_error(
            GenerationErrorCodes.OBJECT_NOT_FOUND,
            "生成对象不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="path",
                    field="object_id",
                    issue="not_found",
                    rejected_value=str(object_id),
                )
            ],
        )

    try:
        from_status = obj.status
        updated_obj = await repo.update_object_status(
            object_id=object_id,
            new_status=body.status.value,
        )
    except ValueError as e:
        if str(e) == "INVALID_OBJECT_STATUS":
            raise_generation_error(
                GenerationErrorCodes.INVALID_OBJECT_STATUS,
                f"生成对象状态 {obj.status} 不允许当前操作",
                request_id,
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
        raise

    record_generated_object_status(updated_obj.status)

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_GENERATED_OBJECT_STATUS_UPDATE,
        resource_type=RESOURCE_GENERATED_OBJECT,
        resource_id=object_id,
        request_payload_jsonb={
            "from_status": from_status,
            "to_status": updated_obj.status,
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=UpdateObjectStatusResponse(
            object_id=updated_obj.object_id,
            status=GeneratedObjectStatus(updated_obj.status),
            request_id_=request_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )


@ops_router.post(
    "/generation/requests/{request_id}/objects",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Request not found"},
    },
    tags=["ops"],
)
async def create_generated_object(
    request_id: uuid.UUID,
    body: CreateGeneratedObjectRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[CreateGeneratedObjectResponse]:
    req_id = _make_request_id("req_ops_create_object")

    repo = GenerationRepository(db)
    gen_req = await repo.get_request_by_id(request_id)
    if gen_req is None:
        raise_generation_error(
            GenerationErrorCodes.REQUEST_NOT_FOUND,
            "生成请求不存在",
            req_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="path",
                    field="request_id",
                    issue="not_found",
                    rejected_value=str(request_id),
                )
            ],
        )

    if gen_req.status not in ["processing"]:
        raise_generation_error(
            GenerationErrorCodes.INVALID_REQUEST_STATUS,
            f"生成请求状态 {gen_req.status} 不允许创建对象",
            req_id,
            status_code=status.HTTP_409_CONFLICT,
            details=[
                ErrorDetail(
                    location="body",
                    field="status",
                    issue="invalid_transition",
                    rejected_value=gen_req.status,
                )
            ],
        )

    if body.quality_score is None:
        score_result = quality_scorer.score(body.object_type, body.object_payload)
        quality_score = score_result.score
    else:
        quality_score = body.quality_score

    obj = await repo.create_generated_object(
        request_id=request_id,
        object_type=body.object_type,
        object_payload=body.object_payload,
        schema_version=body.schema_version,
        quality_score=quality_score,
    )

    record_generated_object_status(obj.status)

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_GENERATED_OBJECT_CREATE,
        resource_type=RESOURCE_GENERATED_OBJECT,
        resource_id=obj.object_id,
        request_payload_jsonb=body.model_dump(mode="json"),
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=req_id,
        data=CreateGeneratedObjectResponse(
            object_id=obj.object_id,
            request_id=obj.request_id,
            object_type=obj.object_type,
            status=GeneratedObjectStatus(obj.status),
            quality_score=obj.quality_score,
            request_id_=req_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )
