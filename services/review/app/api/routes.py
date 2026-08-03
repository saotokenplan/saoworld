import uuid
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import RequireOpsRole, RequireReviewApproveScope, UserPayload
from app.core.errors import ReviewErrorCodes, raise_review_error
from app.core.event_publisher import event_publisher
from app.core.metrics import record_review_create, record_review_duration, record_review_result
from app.core.review_efficiency import collect_review_efficiency
from app.repositories.audit_repo import (
    ACTION_REVIEW_APPROVE,
    ACTION_REVIEW_RECORD_CREATE,
    ACTION_REVIEW_REJECT,
    ACTION_REVIEW_RESULT_UPDATE,
    RESOURCE_REVIEW_RECORD,
    AuditRepository,
)
from app.repositories.review_repo import ReviewRepository
from app.schemas.review import (
    ApproveReviewRequest,
    ApproveReviewResponse,
    AutoReviewRequest,
    AutoReviewResponse,
    CreateReviewRequest,
    CreateReviewResponse,
    EnvelopeResponse,
    ErrorDetail,
    HealthResponse,
    PaginatedMeta,
    RejectReviewRequest,
    RejectReviewResponse,
    ReviewEfficiencyResponse,
    ReviewRecordListResponse,
    ReviewRecordResponse,
    ReviewResult,
    RiskLevel,
    UpdateReviewResultRequest,
    UpdateReviewResultResponse,
)

router = APIRouter()
ops_router = APIRouter()

logger = structlog.get_logger()


def _make_request_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _get_trace_id(request: Request) -> str | None:
    return request.headers.get("X-Trace-Id")


def _duration_since(created_at: datetime | None) -> float:
    """审核耗时（秒）：now(UTC) - created_at。

    兼容 SQLite 测试底座返回 naive 时间戳的场景（不抛 offset-naive/aware 混合相减错误）。
    """
    if created_at is None:
        return 0.0
    now = datetime.now(UTC)
    ref = created_at.replace(tzinfo=UTC) if created_at.tzinfo is None else created_at
    return (now - ref).total_seconds()


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
        raise_review_error(
            ReviewErrorCodes.REVIEW_NOT_FOUND,
            "审核记录不存在",
            req_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="path",
                    field="review_id",
                    issue="not_found",
                    rejected_value=str(review_id),
                )
            ],
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

    record_review_create()

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
        raise_review_error(
            ReviewErrorCodes.REVIEW_NOT_FOUND,
            "审核记录不存在",
            req_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="path",
                    field="review_id",
                    issue="not_found",
                    rejected_value=str(review_id),
                )
            ],
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

        # M1: 记录人工审核耗时（单条审核从创建到本次终结）
        duration = _duration_since(updated_review.created_at)
        record_review_duration("manual", updated_review.object_type, duration)
    except ValueError as e:
        if str(e) == "INVALID_REVIEW_STATUS":
            raise_review_error(
                ReviewErrorCodes.INVALID_REVIEW_STATUS,
                f"审核记录状态 {review.result} 不允许当前操作",
                req_id,
                status_code=status.HTTP_409_CONFLICT,
                details=[
                    ErrorDetail(
                        location="body",
                        field="result",
                        issue="invalid_transition",
                        rejected_value=body.result.value,
                    )
                ],
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
            raise_review_error(
                ReviewErrorCodes.NO_REVIEWS_FOUND,
                "该对象没有审核记录",
                request_id,
                status_code=status.HTTP_404_NOT_FOUND,
                details=[
                    ErrorDetail(
                        location="path",
                        field="object_id",
                        issue="no_reviews",
                        rejected_value=str(object_id),
                    )
                ],
            )
        raise

    if not updated_reviews:
        raise_review_error(
            ReviewErrorCodes.INVALID_REVIEW_STATUS,
            "所有审核记录状态不允许批准操作",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    record_review_result("approved", "manual")

    # M1: 记录人工审核耗时（从创建到本次批准终结）
    for updated_review in updated_reviews:
        duration = _duration_since(updated_review.created_at)
        record_review_duration("manual", updated_review.object_type, duration)

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

    # 事件发布：批量审核完成
    # WP4：携带 content_package_id 时，下游 handle_review_batch_completed
    # 守卫成立并触发全量复审；缺省时保持「仅审核不复审」的既有行为。
    try:
        import uuid
        from datetime import datetime, timezone
        await event_publisher.publish_review_batch_completed(
            batch_id=str(uuid.uuid4()),
            request_id=body.request_id or "",
            content_package_id=(
                str(body.content_package_id)
                if body.content_package_id is not None
                else None
            ),
            approved_count=len(updated_reviews),
            rejected_count=0,
            needs_revision_count=0,
            completed_at=datetime.now(timezone.utc).isoformat(),
            trace_id=x_trace_id or "",
        )
    except Exception as exc:
        logger.error(
            "event_publish_failed",
            event_type="review_batch_completed",
            object_id=str(object_id),
            error=str(exc),
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
            raise_review_error(
                ReviewErrorCodes.NO_REVIEWS_FOUND,
                "该对象没有审核记录",
                request_id,
                status_code=status.HTTP_404_NOT_FOUND,
                details=[
                    ErrorDetail(
                        location="path",
                        field="object_id",
                        issue="no_reviews",
                        rejected_value=str(object_id),
                    )
                ],
            )
        raise

    if not updated_reviews:
        raise_review_error(
            ReviewErrorCodes.INVALID_REVIEW_STATUS,
            "所有审核记录状态不允许拒绝操作",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    record_review_result("rejected", "manual")

    # M1: 记录人工审核耗时（从创建到本次拒绝终结）
    for updated_review in updated_reviews:
        duration = _duration_since(updated_review.created_at)
        record_review_duration("manual", updated_review.object_type, duration)

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

    # 事件发布：批量审核完成
    # 拒绝路径 approved_count 恒为 0，下游守卫不会触发复审；
    # 携带内容包引用仅用于事件溯源，口径与批准路径保持一致。
    try:
        import uuid
        from datetime import datetime, timezone
        await event_publisher.publish_review_batch_completed(
            batch_id=str(uuid.uuid4()),
            request_id=body.request_id or "",
            content_package_id=(
                str(body.content_package_id)
                if body.content_package_id is not None
                else None
            ),
            approved_count=0,
            rejected_count=len(updated_reviews),
            needs_revision_count=0,
            completed_at=datetime.now(timezone.utc).isoformat(),
            trace_id=x_trace_id or "",
        )
    except Exception as exc:
        logger.error(
            "event_publish_failed",
            event_type="review_batch_completed",
            object_id=str(object_id),
            error=str(exc),
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


@ops_router.post(
    "/review/auto",
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["ops"],
)
async def auto_review(
    body: AutoReviewRequest,
    request: Request,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[AutoReviewResponse]:
    from app.core.auto_review_engine import auto_review_engine

    request_id = _make_request_id("req_ops_auto_review")
    trace_id = x_trace_id or _make_request_id("trace")

    try:
        result = auto_review_engine.evaluate(
            object_type=body.object_type,
            object_payload=body.object_payload,
            quality_score=body.quality_score,
        )

        repo = ReviewRepository(db)
        risk_level = "low" if result["auto_result"] == "approved" else "medium"
        if result["auto_result"] == "rejected":
            risk_level = "high"

        review = await repo.create_review(
            object_id=body.object_id,
            object_type=body.object_type,
            review_type="auto",
            trace_id=body.trace_id,
            quality_score=body.quality_score,
            detail={
                "auto_result": result["auto_result"],
                "reason": result["reason"],
                "rule_results": result["rule_results"],
                "is_automatic": result["is_automatic"],
            },
            result=result["auto_result"],
            risk_level=risk_level,
        )

        record_review_create()

        # M1: 记录审核耗时（auto 路径创建即终结，时长近似引擎处理耗时）
        duration = _duration_since(review.created_at)
        record_review_duration("auto", body.object_type, duration)

        # M2: auto 路径对所有终局判定统一计数（含 manual_review），并标记 review_type=auto
        record_review_result(result["auto_result"], "auto")

        audit_repo = AuditRepository(db)
        await audit_repo.create_audit_log(
            trace_id=trace_id,
            operator_id=current_user.user_id,
            operator_role=current_user.role.value,
            action=ACTION_REVIEW_RECORD_CREATE,
            resource_type=RESOURCE_REVIEW_RECORD,
            resource_id=review.review_id,
            request_payload_jsonb={
                "object_id": str(body.object_id),
                "object_type": body.object_type,
                "auto_result": result["auto_result"],
                "is_automatic": result["is_automatic"],
                "reason": result["reason"],
            },
            result_status=200,
        )

        # WP4 事件发布：自动审核通过 → 发布队列串联
        # 仅在判定为 approved 且请求携带 content_package_id 时发布；
        # 沿用既有容错惯例，事件发布失败不影响审核主流程。
        if result["auto_result"] == "approved":
            if body.content_package_id is not None:
                try:
                    await event_publisher.publish_review_auto_approved(
                        object_id=str(body.object_id),
                        object_type=body.object_type,
                        content_package_id=str(body.content_package_id),
                        approved_at=review.created_at.isoformat(),
                        quality_score=body.quality_score,
                        risk_level=risk_level,
                        trace_id=trace_id,
                    )
                except Exception as exc:
                    logger.error(
                        "event_publish_failed",
                        event_type="review_auto_approved",
                        object_id=str(body.object_id),
                        content_package_id=str(body.content_package_id),
                        error=str(exc),
                    )
            else:
                logger.info(
                    "auto_approved_without_content_package",
                    object_id=str(body.object_id),
                    object_type=body.object_type,
                    trace_id=trace_id,
                )

        return EnvelopeResponse(
            request_id=request_id,
            data=AutoReviewResponse(
                object_id=body.object_id,
                auto_result=result["auto_result"],
                reason=result["reason"],
                is_automatic=result["is_automatic"],
                rule_results=[
                    {"rule": r["rule"], "result": r["result"], "error": r.get("error")}
                    for r in result["rule_results"]
                ],
                request_id_=request_id,
                trace_id=trace_id,
            ),
            trace_id=trace_id,
        )

    except Exception as e:
        logger.error(
            "auto_review_failed",
            error=str(e),
            request_id=request_id,
            trace_id=trace_id,
        )
        raise_review_error(
            ReviewErrorCodes.INTERNAL_ERROR,
            f"自动审核失败: {str(e)}",
            request_id,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get(
    "/review/stats",
    responses={503: {"description": "指标采集不可用"}},
    tags=["review"],
)
async def get_review_efficiency_stats(
    request: Request,
) -> EnvelopeResponse[ReviewEfficiencyResponse]:
    """审核效率派生指标（WP3 ops 看板三字段数据源）。

    供 ops-service 内部调用，从 review 服务 Prometheus 指标派生：
    - auto_pass_rate: 自动审核通过率
    - manual_intervention_rate: 人工介入率
    - review_p95_minutes: 审核耗时 P95（分钟）

    无鉴权：属内部服务间调用（ops 不携带鉴权头调用本端点）。
    """
    request_id = _make_request_id("req")
    trace_id = _get_trace_id(request)
    data = collect_review_efficiency()
    return EnvelopeResponse(
        request_id=request_id,
        data=ReviewEfficiencyResponse(**data),
        trace_id=trace_id,
    )
