import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import RequireOpsRole, RequireReviewApproveScope, UserPayload
from app.repositories.audit_repo import (
    ACTION_REVIEW_APPROVE,
    ACTION_REVIEW_REJECT,
    ACTION_REVIEW_RECORD_CREATE,
    ACTION_REVIEW_RESULT_UPDATE,
    RESOURCE_REVIEW_RECORD,
    AuditRepository,
)
from app.repositories.review_repo import ReviewRepository
from app.schemas.review import (
    ApproveReviewRequest,
    ApproveReviewResponse,
    CreateReviewRequest,
    CreateReviewResponse,
    EnvelopeResponse,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    PaginatedMeta,
    RejectReviewRequest,
    RejectReviewResponse,
    ReviewRecordListResponse,
    ReviewRecordResponse,
    ReviewResult,
    RiskLevel,
    UpdateReviewResultRequest,
    UpdateReviewResultResponse,
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


@ops_router.get(
    "/review/records",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["ops"],
)
async def list_review_records(
    request: Request,
    object_type: str | None = Query(default=None, max_length=64),
    result_filter: ReviewResult | None = Query(default=None, alias="result"),
    risk_level_filter: RiskLevel | None = Query(default=None, alias="risk_level"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireOpsRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[ReviewRecordListResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_review_records_list")

    repo = ReviewRepository(db)
    reviews, total = await repo.list_reviews(
        object_type=object_type,
        result=result_filter.value if result_filter else None,
        risk_level=risk_level_filter.value if risk_level_filter else None,
        limit=limit,
        offset=offset,
    )

    review_responses = [
        ReviewRecordResponse(
            review_id=review.review_id,
            object_id=review.object_id,
            object_type=review.object_type,
            review_type=review.review_type,
            result=ReviewResult(review.result),
            risk_level=RiskLevel(review.risk_level),
            quality_score=review.quality_score,
            detail=review.detail_jsonb,
            operator_id=review.operator_id,
            operator_role=review.operator_role,
            reason=review.reason,
            trace_id=review.trace_id,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )
        for review in reviews
    ]

    return EnvelopeResponse(
        request_id=request_id,
        data=ReviewRecordListResponse(reviews=review_responses, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@ops_router.get(
    "/review/records/{review_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Review not found"},
    },
    tags=["ops"],
)
async def get_review_record_detail(
    review_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireOpsRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[ReviewRecordResponse]:
    trace_id = _get_trace_id(request)
    req_id = _make_request_id("req_review_record_detail")

    repo = ReviewRepository(db)
    review = await repo.get_review_by_id(review_id)

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="REVIEW_NOT_FOUND",
                message="审核记录不存在",
                request_id=req_id,
                details=[
                    ErrorDetail(
                        location="path",
                        field="review_id",
                        issue="not_found",
                        rejected_value=str(review_id),
                    )
                ],
            ).model_dump(),
        )

    return EnvelopeResponse(
        request_id=req_id,
        data=ReviewRecordResponse(
            review_id=review.review_id,
            object_id=review.object_id,
            object_type=review.object_type,
            review_type=review.review_type,
            result=ReviewResult(review.result),
            risk_level=RiskLevel(review.risk_level),
            quality_score=review.quality_score,
            detail=review.detail_jsonb,
            operator_id=review.operator_id,
            operator_role=review.operator_role,
            reason=review.reason,
            trace_id=review.trace_id,
            created_at=review.created_at,
            updated_at=review.updated_at,
        ),
        trace_id=trace_id,
    )


@ops_router.post(
    "/review/records",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["ops"],
)
async def create_review_record(
    body: CreateReviewRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[CreateReviewResponse]:
    request_id = _make_request_id("req_ops_review_record")

    repo = ReviewRepository(db)
    review = await repo.create_review(
        object_id=body.object_id,
        object_type=body.object_type,
        review_type=body.review_type,
        trace_id=body.trace_id,
        quality_score=body.quality_score,
        detail=body.detail,
        result=body.result.value,
        risk_level=body.risk_level.value,
    )

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_REVIEW_RECORD_CREATE,
        resource_type=RESOURCE_REVIEW_RECORD,
        resource_id=review.review_id,
        request_payload_jsonb=body.model_dump(mode="json"),
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=CreateReviewResponse(
            review_id=review.review_id,
            object_id=review.object_id,
            result=ReviewResult(review.result),
            request_id_=request_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )


@ops_router.post(
    "/review/records/{review_id}/result",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Review not found"},
        409: {"description": "Invalid state transition"},
    },
    tags=["ops"],
)
async def update_review_result(
    review_id: uuid.UUID,
    body: UpdateReviewResultRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireReviewApproveScope,
) -> EnvelopeResponse[UpdateReviewResultResponse]:
    req_id = _make_request_id("req_ops_review_result")

    repo = ReviewRepository(db)
    review = await repo.get_review_by_id(review_id)

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="REVIEW_NOT_FOUND",
                message="审核记录不存在",
                request_id=req_id,
                details=[
                    ErrorDetail(
                        location="path",
                        field="review_id",
                        issue="not_found",
                        rejected_value=str(review_id),
                    )
                ],
            ).model_dump(),
        )

    try:
        from_status = review.result
        updated_review = await repo.update_review_result(
            review_id=review_id,
            result=body.result.value,
            risk_level=body.risk_level.value if body.risk_level else None,
            reason=body.reason,
            operator_id=current_user.user_id,
            operator_role=current_user.role.value,
        )
    except ValueError as e:
        if str(e) == "INVALID_REVIEW_STATUS":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorResponse(
                    code="INVALID_REVIEW_STATUS",
                    message=f"审核记录状态 {review.result} 不允许当前操作",
                    request_id=req_id,
                    details=[
                        ErrorDetail(
                            location="body",
                            field="result",
                            issue="invalid_transition",
                            rejected_value=body.result.value,
                        )
                    ],
                ).model_dump(),
            )
        raise

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_REVIEW_RESULT_UPDATE,
        resource_type=RESOURCE_REVIEW_RECORD,
        resource_id=review_id,
        request_payload_jsonb={
            "from_status": from_status,
            "to_status": updated_review.result,
            "reason": body.reason,
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=req_id,
        data=UpdateReviewResultResponse(
            review_id=updated_review.review_id,
            object_id=updated_review.object_id,
            result=ReviewResult(updated_review.result),
            risk_level=RiskLevel(updated_review.risk_level),
            request_id_=req_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )


@ops_router.post(
    "/review/{object_id}/approve",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "No reviews found for object"},
        409: {"description": "Invalid state transition"},
    },
    tags=["ops"],
)
async def approve_review_object(
    object_id: uuid.UUID,
    body: ApproveReviewRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireReviewApproveScope,
) -> EnvelopeResponse[ApproveReviewResponse]:
    request_id = _make_request_id("req_ops_review_approve")

    repo = ReviewRepository(db)

    try:
        updated_reviews = await repo.approve_by_object_id(
            object_id=object_id,
            operator_id=current_user.user_id,
            operator_role=current_user.role.value,
            reason=body.reason,
        )
    except ValueError as e:
        if str(e) == "NO_REVIEWS_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    code="NO_REVIEWS_FOUND",
                    message="该对象没有审核记录",
                    request_id=request_id,
                    details=[
                        ErrorDetail(
                            location="path",
                            field="object_id",
                            issue="no_reviews",
                            rejected_value=str(object_id),
                        )
                    ],
                ).model_dump(),
            )
        raise

    if not updated_reviews:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                code="INVALID_REVIEW_STATUS",
                message="所有审核记录状态不允许批准操作",
                request_id=request_id,
            ).model_dump(),
        )

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_REVIEW_APPROVE,
        resource_type=RESOURCE_REVIEW_RECORD,
        resource_id=None,
        reason=body.reason,
        request_payload_jsonb={
            "object_id": str(object_id),
            "updated_reviews_count": len(updated_reviews),
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=ApproveReviewResponse(
            object_id=object_id,
            result=ReviewResult.APPROVED,
            request_id_=request_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )


@ops_router.post(
    "/review/{object_id}/reject",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "No reviews found for object"},
        409: {"description": "Invalid state transition"},
    },
    tags=["ops"],
)
async def reject_review_object(
    object_id: uuid.UUID,
    body: RejectReviewRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireReviewApproveScope,
) -> EnvelopeResponse[RejectReviewResponse]:
    request_id = _make_request_id("req_ops_review_reject")

    repo = ReviewRepository(db)

    try:
        updated_reviews = await repo.reject_by_object_id(
            object_id=object_id,
            operator_id=current_user.user_id,
            operator_role=current_user.role.value,
            reason=body.reason,
            risk_level=body.risk_level.value,
        )
    except ValueError as e:
        if str(e) == "NO_REVIEWS_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    code="NO_REVIEWS_FOUND",
                    message="该对象没有审核记录",
                    request_id=request_id,
                    details=[
                        ErrorDetail(
                            location="path",
                            field="object_id",
                            issue="no_reviews",
                            rejected_value=str(object_id),
                        )
                    ],
                ).model_dump(),
            )
        raise

    if not updated_reviews:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                code="INVALID_REVIEW_STATUS",
                message="所有审核记录状态不允许拒绝操作",
                request_id=request_id,
            ).model_dump(),
        )

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_REVIEW_REJECT,
        resource_type=RESOURCE_REVIEW_RECORD,
        resource_id=None,
        reason=body.reason,
        request_payload_jsonb={
            "object_id": str(object_id),
            "risk_level": body.risk_level.value,
            "updated_reviews_count": len(updated_reviews),
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=RejectReviewResponse(
            object_id=object_id,
            result=ReviewResult.REJECTED,
            risk_level=body.risk_level,
            request_id_=request_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )