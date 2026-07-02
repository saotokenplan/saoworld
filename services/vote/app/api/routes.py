import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    RequireOpsScope,
    RequireVotesHistoryReadScope,
    RequireVotesReadScope,
    RequireVotesSubmitScope,
    UserPayload,
)
from app.repositories.audit_repo import (
    ACTION_VOTE_CYCLE_CREATE,
    ACTION_VOTE_CYCLE_TRANSITION,
    ACTION_VOTE_SUBMIT,
    RESOURCE_VOTE,
    RESOURCE_VOTE_CYCLE,
    AuditRepository,
)
from app.repositories.vote_repo import VoteRepository
from app.schemas.vote import (
    CandidateResponse,
    CreateVoteCycleRequest,
    CreateVoteCycleResponse,
    CurrentVoteResponse,
    EnvelopeResponse,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    PaginatedMeta,
    TransitionVoteCycleRequest,
    TransitionVoteCycleResponse,
    VoteHistoryItem,
    VoteHistoryResponse,
    VoteSubmitRequest,
    VoteSubmitResponse,
)

router = APIRouter()
ops_router = APIRouter()


def _make_request_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _get_trace_id(request: Request) -> str | None:
    """从请求头获取 trace_id。"""
    return request.headers.get("X-Trace-Id")


async def _log_transition_audit(
    db: AsyncSession,
    *,
    trace_id: str | None,
    operator_id: str,
    operator_role: str,
    vote_cycle_id: uuid.UUID,
    from_status: str,
    to_status: str,
    reason: str | None = None,
    result_status: int = 200,
) -> None:
    """记录投票周期状态迁移审计日志。"""
    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        operator_id=operator_id,
        operator_role=operator_role,
        action=ACTION_VOTE_CYCLE_TRANSITION,
        resource_type=RESOURCE_VOTE_CYCLE,
        resource_id=vote_cycle_id,
        reason=reason,
        request_payload_jsonb={"from_status": from_status, "to_status": to_status},
        result_status=result_status,
    )


# --- 健康检查 ---


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


# --- 玩家投票接口 ---


@router.get(
    "/votes/current",
    responses={
        404: {"description": "No open vote cycle"},
    },
    tags=["votes"],
)
async def get_current_vote(
    request: Request,
    current_user: UserPayload = RequireVotesReadScope,
    x_player_id: str | None = Header(default=None, alias="X-Player-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[CurrentVoteResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_vote_current")

    # 优先使用 JWT 中的 user_id，兼容 X-Player-Id
    player_id_str = current_user.user_id

    repo = VoteRepository(db)
    cycle = await repo.get_current_open_cycle()

    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="NO_OPEN_VOTE_CYCLE",
                message="当前没有开放的投票周期",
                request_id=request_id,
            ).model_dump(),
        )

    candidates = await repo.get_candidates_for_cycle(cycle.vote_cycle_id)
    candidate_responses = [CandidateResponse.model_validate(c) for c in candidates]

    has_voted = False
    my_vote_candidate_id = None

    try:
        player_uuid = uuid.UUID(player_id_str)
        existing_vote = await repo.has_player_voted(cycle.vote_cycle_id, player_uuid)
        if existing_vote is not None:
            has_voted = True
            my_vote_candidate_id = existing_vote.candidate_id
    except ValueError:
        pass

    return EnvelopeResponse(
        request_id=request_id,
        data=CurrentVoteResponse(
            vote_cycle_id=cycle.vote_cycle_id,
            chapter_id=cycle.chapter_id,
            status=cycle.status,
            starts_at=cycle.starts_at,
            ends_at=cycle.ends_at,
            candidates=candidate_responses,
            has_voted=has_voted,
            my_vote_candidate_id=my_vote_candidate_id,
        ),
        trace_id=trace_id,
    )


@router.post(
    "/votes/submit",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid request"},
        404: {"description": "Vote cycle or candidate not found"},
        409: {"description": "Duplicate vote or state conflict"},
        422: {"description": "Validation error"},
    },
    tags=["votes"],
)
async def submit_vote(
    body: VoteSubmitRequest,
    request: Request,
    current_user: UserPayload = RequireVotesSubmitScope,
    x_player_id: str | None = Header(default=None, alias="X-Player-Id"),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[VoteSubmitResponse]:
    request_id = _make_request_id("req_vote_submit")

    # 优先使用 JWT 中的 user_id，兼容 X-Player-Id
    player_id_str = current_user.user_id

    try:
        player_uuid = uuid.UUID(player_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code="INVALID_PLAYER_ID",
                message="无效的玩家ID格式",
                request_id=request_id,
                details=[
                    ErrorDetail(
                        location="token",
                        field="sub",
                        issue="invalid_uuid",
                        rejected_value=player_id_str,
                    )
                ],
            ).model_dump(),
        )

    repo = VoteRepository(db)

    existing_by_key = await repo.vote_exists_by_idempotency_key(idempotency_key)
    if existing_by_key is not None:
        return EnvelopeResponse(
            request_id=_make_request_id("req_vote_submit_idempotent"),
            data=VoteSubmitResponse(
                vote_id=existing_by_key.vote_id,
                vote_cycle_id=existing_by_key.vote_cycle_id,
                candidate_id=existing_by_key.candidate_id,
                submitted_at=existing_by_key.created_at,
                request_id=request_id,
                trace_id=x_trace_id,
            ),
            trace_id=x_trace_id,
        )

    cycle = await repo.get_current_open_cycle()
    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                code="INVALID_VOTE_STATE",
                message="当前投票周期不可投票",
                request_id=request_id,
            ).model_dump(),
        )

    candidate = await repo.get_candidate_by_id(body.candidate_id)
    if candidate is None or candidate.vote_cycle_id != cycle.vote_cycle_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="CANDIDATE_NOT_FOUND",
                message="候选项不存在或不属于当前投票周期",
                request_id=request_id,
                details=[
                    ErrorDetail(
                        location="body",
                        field="candidate_id",
                        issue="not_found",
                        rejected_value=str(body.candidate_id),
                    )
                ],
            ).model_dump(),
        )

    if candidate.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                code="CANDIDATE_NOT_ACTIVE",
                message="该候选项当前不可投票",
                request_id=request_id,
            ).model_dump(),
        )

    existing_vote = await repo.has_player_voted(cycle.vote_cycle_id, player_uuid)
    if existing_vote is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                code="ALREADY_VOTED",
                message="你已经在本周期投过票",
                request_id=request_id,
            ).model_dump(),
        )

    vote = await repo.create_vote(
        vote_cycle_id=cycle.vote_cycle_id,
        player_id=player_uuid,
        candidate_id=body.candidate_id,
        weight=body.weight,
        device_fingerprint_hash=body.device_fingerprint_hash,
        idempotency_key=idempotency_key,
    )

    # 审计日志：投票提交
    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=str(player_uuid),
        operator_role="player",
        action=ACTION_VOTE_SUBMIT,
        resource_type=RESOURCE_VOTE,
        resource_id=vote.vote_id,
        request_payload_jsonb={"candidate_id": str(body.candidate_id), "weight": body.weight},
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=VoteSubmitResponse(
            vote_id=vote.vote_id,
            vote_cycle_id=vote.vote_cycle_id,
            candidate_id=vote.candidate_id,
            submitted_at=vote.created_at or datetime.now(timezone.utc),
            request_id=request_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )


@router.get(
    "/votes/history",
    responses={
        400: {"description": "Invalid player ID"},
    },
    tags=["votes"],
)
async def get_vote_history(
    request: Request,
    current_user: UserPayload = RequireVotesHistoryReadScope,
    x_player_id: str | None = Header(default=None, alias="X-Player-Id"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[VoteHistoryResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_vote_history")

    # 优先使用 JWT 中的 user_id
    player_id_str = current_user.user_id

    try:
        player_uuid = uuid.UUID(player_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code="INVALID_PLAYER_ID",
                message="无效的玩家ID格式",
                request_id=request_id,
                details=[
                    ErrorDetail(
                        location="token",
                        field="sub",
                        issue="invalid_uuid",
                        rejected_value=player_id_str,
                    )
                ],
            ).model_dump(),
        )

    repo = VoteRepository(db)
    rows, total = await repo.get_vote_history(player_uuid, limit=limit, offset=offset)

    vote_items = [
        VoteHistoryItem(
            vote_id=v.vote_id,
            vote_cycle_id=v.vote_cycle_id,
            candidate_id=v.candidate_id,
            candidate_title=c.title,
            weight=v.weight,
            created_at=v.created_at,
        )
        for v, c in rows
    ]

    return EnvelopeResponse(
        request_id=request_id,
        data=VoteHistoryResponse(
            player_id=player_uuid,
            votes=vote_items,
            total=total,
        ),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


# --- 运营写接口 ---


@ops_router.post(
    "/vote-cycles",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        409: {"description": "Conflict"},
    },
    tags=["ops"],
)
async def create_vote_cycle(
    body: CreateVoteCycleRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsScope,
) -> EnvelopeResponse[CreateVoteCycleResponse]:
    request_id = _make_request_id("req_ops_vc")

    if body.ends_at <= body.starts_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code="INVALID_ARGUMENT",
                message="投票结束时间必须晚于开始时间",
                request_id=request_id,
                details=[
                    ErrorDetail(
                        location="body",
                        field="ends_at",
                        issue="must_be_after_starts_at",
                        rejected_value=body.ends_at.isoformat(),
                    )
                ],
            ).model_dump(),
        )

    repo = VoteRepository(db)

    existing_open = await repo.get_open_cycle_for_chapter(body.chapter_id)
    if existing_open is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                code="VOTE_CYCLE_CONFLICT",
                message="当前章节已存在开放中的投票周期",
                request_id=request_id,
            ).model_dump(),
        )

    candidates_data = [c.model_dump() for c in body.candidates]
    cycle = await repo.create_vote_cycle(
        chapter_id=body.chapter_id,
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        created_by=current_user.user_id,
        created_reason=body.reason,
        candidates_data=candidates_data,
    )

    # 重新加载以获取 candidates 关系
    loaded_cycle = await repo.get_cycle_by_id(cycle.vote_cycle_id)
    candidates_resp = [CandidateResponse.model_validate(c) for c in loaded_cycle.candidates]

    # 审计日志：投票周期创建
    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        request_id=None,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_VOTE_CYCLE_CREATE,
        resource_type=RESOURCE_VOTE_CYCLE,
        resource_id=cycle.vote_cycle_id,
        reason=body.reason,
        request_payload_jsonb=body.model_dump(mode="json"),
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=CreateVoteCycleResponse(
            vote_cycle_id=cycle.vote_cycle_id,
            chapter_id=cycle.chapter_id,
            status=cycle.status,
            starts_at=cycle.starts_at,
            ends_at=cycle.ends_at,
            candidates=candidates_resp,
            request_id=request_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )


@ops_router.post(
    "/vote-cycles/{vote_cycle_id}/schedule",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Vote cycle not found"},
        409: {"description": "Invalid state transition"},
    },
    tags=["ops"],
)
async def schedule_vote_cycle(
    vote_cycle_id: uuid.UUID,
    body: TransitionVoteCycleRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsScope,
) -> EnvelopeResponse[TransitionVoteCycleResponse]:
    request_id = _make_request_id("req_ops_vc_schedule")

    repo = VoteRepository(db)

    cycle = await repo.get_cycle_by_id(vote_cycle_id)
    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="VOTE_CYCLE_NOT_FOUND",
                message="投票周期不存在",
                request_id=request_id,
            ).model_dump(),
        )

    if not VoteRepository.is_valid_transition(cycle.status, "scheduled"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                code="INVALID_VOTE_STATE",
                message=f"投票周期状态 {cycle.status} 不允许迁移到 scheduled",
                request_id=request_id,
            ).model_dump(),
        )

    from_status = cycle.status
    updated_cycle = await repo.transition_cycle_status(vote_cycle_id, "scheduled")

    await _log_transition_audit(
        db,
        trace_id=x_trace_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        vote_cycle_id=vote_cycle_id,
        from_status=from_status,
        to_status="scheduled",
        reason=body.reason,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=TransitionVoteCycleResponse(
            vote_cycle_id=updated_cycle.vote_cycle_id,
            status=updated_cycle.status,
            request_id=request_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )


@ops_router.post(
    "/vote-cycles/{vote_cycle_id}/open",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Vote cycle not found"},
        409: {"description": "Invalid state transition"},
    },
    tags=["ops"],
)
async def open_vote_cycle(
    vote_cycle_id: uuid.UUID,
    body: TransitionVoteCycleRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsScope,
) -> EnvelopeResponse[TransitionVoteCycleResponse]:
    request_id = _make_request_id("req_ops_vc_open")

    repo = VoteRepository(db)

    cycle = await repo.get_cycle_by_id(vote_cycle_id)
    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="VOTE_CYCLE_NOT_FOUND",
                message="投票周期不存在",
                request_id=request_id,
            ).model_dump(),
        )

    if not VoteRepository.is_valid_transition(cycle.status, "open"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                code="INVALID_VOTE_STATE",
                message=f"投票周期状态 {cycle.status} 不允许迁移到 open",
                request_id=request_id,
            ).model_dump(),
        )

    # 检查同一章节是否已有开放周期
    existing_open = await repo.get_open_cycle_for_chapter(cycle.chapter_id)
    if existing_open is not None and existing_open.vote_cycle_id != vote_cycle_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                code="VOTE_CYCLE_CONFLICT",
                message="当前章节已存在开放中的投票周期",
                request_id=request_id,
            ).model_dump(),
        )

    from_status = cycle.status
    updated_cycle = await repo.transition_cycle_status(vote_cycle_id, "open")

    await _log_transition_audit(
        db,
        trace_id=x_trace_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        vote_cycle_id=vote_cycle_id,
        from_status=from_status,
        to_status="open",
        reason=body.reason,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=TransitionVoteCycleResponse(
            vote_cycle_id=updated_cycle.vote_cycle_id,
            status=updated_cycle.status,
            request_id=request_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )


@ops_router.post(
    "/vote-cycles/{vote_cycle_id}/close",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Vote cycle not found"},
        409: {"description": "Invalid state transition"},
    },
    tags=["ops"],
)
async def close_vote_cycle(
    vote_cycle_id: uuid.UUID,
    body: TransitionVoteCycleRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsScope,
) -> EnvelopeResponse[TransitionVoteCycleResponse]:
    request_id = _make_request_id("req_ops_vc_close")

    repo = VoteRepository(db)

    cycle = await repo.get_cycle_by_id(vote_cycle_id)
    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="VOTE_CYCLE_NOT_FOUND",
                message="投票周期不存在",
                request_id=request_id,
            ).model_dump(),
        )

    if not VoteRepository.is_valid_transition(cycle.status, "closed"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                code="INVALID_VOTE_STATE",
                message=f"投票周期状态 {cycle.status} 不允许迁移到 closed",
                request_id=request_id,
            ).model_dump(),
        )

    # 关闭投票时自动计票
    tally_result = await repo.tally_votes(vote_cycle_id)
    winning_candidate_id = tally_result["winning_candidate_id"]

    from_status = cycle.status
    updated_cycle = await repo.transition_cycle_status(vote_cycle_id, "closed")
    if winning_candidate_id is not None:
        updated_cycle.winning_candidate_id = winning_candidate_id

    await _log_transition_audit(
        db,
        trace_id=x_trace_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        vote_cycle_id=vote_cycle_id,
        from_status=from_status,
        to_status="closed",
        reason=body.reason,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=TransitionVoteCycleResponse(
            vote_cycle_id=updated_cycle.vote_cycle_id,
            status=updated_cycle.status,
            winning_candidate_id=winning_candidate_id,
            request_id=request_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )


@ops_router.post(
    "/vote-cycles/{vote_cycle_id}/finalize",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Vote cycle not found"},
        409: {"description": "Invalid state transition"},
    },
    tags=["ops"],
)
async def finalize_vote_cycle(
    vote_cycle_id: uuid.UUID,
    body: TransitionVoteCycleRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsScope,
) -> EnvelopeResponse[TransitionVoteCycleResponse]:
    request_id = _make_request_id("req_ops_vc_finalize")

    repo = VoteRepository(db)

    cycle = await repo.get_cycle_by_id(vote_cycle_id)
    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="VOTE_CYCLE_NOT_FOUND",
                message="投票周期不存在",
                request_id=request_id,
            ).model_dump(),
        )

    if not VoteRepository.is_valid_transition(cycle.status, "finalized"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                code="INVALID_VOTE_STATE",
                message=f"投票周期状态 {cycle.status} 不允许迁移到 finalized",
                request_id=request_id,
            ).model_dump(),
        )

    from_status = cycle.status
    updated_cycle = await repo.transition_cycle_status(vote_cycle_id, "finalized")
    updated_cycle.finalized_at = datetime.now(timezone.utc)

    await _log_transition_audit(
        db,
        trace_id=x_trace_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        vote_cycle_id=vote_cycle_id,
        from_status=from_status,
        to_status="finalized",
        reason=body.reason,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=TransitionVoteCycleResponse(
            vote_cycle_id=updated_cycle.vote_cycle_id,
            status=updated_cycle.status,
            winning_candidate_id=updated_cycle.winning_candidate_id,
            request_id=request_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )
