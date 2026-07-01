import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.repositories.vote_repo import VoteRepository
from app.schemas.vote import (
    CandidateResponse,
    CreateVoteCycleRequest,
    CreateVoteCycleResponse,
    CurrentVoteResponse,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
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


# --- 健康检查 ---


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    from app.core.config import settings

    return HealthResponse(
        service=settings.app_name,
        version=settings.app_version,
    )


# --- 玩家投票接口 ---


@router.get(
    "/votes/current",
    response_model=CurrentVoteResponse,
    responses={
        404: {"model": ErrorResponse, "description": "No open vote cycle"},
    },
    tags=["votes"],
)
async def get_current_vote(
    request: Request,
    x_player_id: str | None = Header(default=None, alias="X-Player-Id"),
    db: AsyncSession = Depends(get_db),
) -> CurrentVoteResponse:
    repo = VoteRepository(db)
    cycle = await repo.get_current_open_cycle()

    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="NO_OPEN_VOTE_CYCLE",
                message="当前没有开放的投票周期",
                request_id=_make_request_id("req_vote_current_404"),
            ).model_dump(),
        )

    candidates = await repo.get_candidates_for_cycle(cycle.vote_cycle_id)
    candidate_responses = [CandidateResponse.model_validate(c) for c in candidates]

    has_voted = False
    my_vote_candidate_id = None

    if x_player_id:
        try:
            player_uuid = uuid.UUID(x_player_id)
            existing_vote = await repo.has_player_voted(cycle.vote_cycle_id, player_uuid)
            if existing_vote is not None:
                has_voted = True
                my_vote_candidate_id = existing_vote.candidate_id
        except ValueError:
            pass

    return CurrentVoteResponse(
        vote_cycle_id=cycle.vote_cycle_id,
        chapter_id=cycle.chapter_id,
        status=cycle.status,
        starts_at=cycle.starts_at,
        ends_at=cycle.ends_at,
        candidates=candidate_responses,
        has_voted=has_voted,
        my_vote_candidate_id=my_vote_candidate_id,
    )


@router.post(
    "/votes/submit",
    response_model=VoteSubmitResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Vote cycle or candidate not found"},
        409: {"model": ErrorResponse, "description": "Duplicate vote or state conflict"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
    tags=["votes"],
)
async def submit_vote(
    body: VoteSubmitRequest,
    request: Request,
    x_player_id: str = Header(..., alias="X-Player-Id"),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> VoteSubmitResponse:
    try:
        player_uuid = uuid.UUID(x_player_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code="INVALID_PLAYER_ID",
                message="无效的玩家ID格式",
                request_id=_make_request_id("req_vote_submit_400"),
                details=[
                    ErrorDetail(
                        location="header",
                        field="X-Player-Id",
                        issue="invalid_uuid",
                        rejected_value=x_player_id,
                    )
                ],
            ).model_dump(),
        )

    repo = VoteRepository(db)

    existing_by_key = await repo.vote_exists_by_idempotency_key(idempotency_key)
    if existing_by_key is not None:
        return VoteSubmitResponse(
            vote_id=existing_by_key.vote_id,
            vote_cycle_id=existing_by_key.vote_cycle_id,
            candidate_id=existing_by_key.candidate_id,
            submitted_at=existing_by_key.created_at,
            request_id=_make_request_id("req_vote_submit_idempotent"),
            trace_id=x_trace_id,
        )

    cycle = await repo.get_current_open_cycle()
    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                code="INVALID_VOTE_STATE",
                message="当前投票周期不可投票",
                request_id=_make_request_id("req_vote_submit_409"),
            ).model_dump(),
        )

    candidate = await repo.get_candidate_by_id(body.candidate_id)
    if candidate is None or candidate.vote_cycle_id != cycle.vote_cycle_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="CANDIDATE_NOT_FOUND",
                message="候选项不存在或不属于当前投票周期",
                request_id=_make_request_id("req_vote_submit_404"),
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
                request_id=_make_request_id("req_vote_submit_409_cand"),
            ).model_dump(),
        )

    existing_vote = await repo.has_player_voted(cycle.vote_cycle_id, player_uuid)
    if existing_vote is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                code="ALREADY_VOTED",
                message="你已经在本周期投过票",
                request_id=_make_request_id("req_vote_submit_409_dup"),
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

    request_id = _make_request_id("req_vote_submit")
    return VoteSubmitResponse(
        vote_id=vote.vote_id,
        vote_cycle_id=vote.vote_cycle_id,
        candidate_id=vote.candidate_id,
        submitted_at=vote.created_at or datetime.now(timezone.utc),
        request_id=request_id,
        trace_id=x_trace_id,
    )


@router.get(
    "/votes/history",
    response_model=VoteHistoryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid player ID"},
    },
    tags=["votes"],
)
async def get_vote_history(
    request: Request,
    x_player_id: str = Header(..., alias="X-Player-Id"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> VoteHistoryResponse:
    try:
        player_uuid = uuid.UUID(x_player_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code="INVALID_PLAYER_ID",
                message="无效的玩家ID格式",
                request_id=_make_request_id("req_vote_history_400"),
                details=[
                    ErrorDetail(
                        location="header",
                        field="X-Player-Id",
                        issue="invalid_uuid",
                        rejected_value=x_player_id,
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

    return VoteHistoryResponse(
        player_id=player_uuid,
        votes=vote_items,
        total=total,
    )


# --- 运营写接口 ---


@ops_router.post(
    "/vote-cycles",
    response_model=CreateVoteCycleResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        409: {"model": ErrorResponse, "description": "Conflict"},
    },
    tags=["ops"],
)
async def create_vote_cycle(
    body: CreateVoteCycleRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> CreateVoteCycleResponse:
    if body.ends_at <= body.starts_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code="INVALID_ARGUMENT",
                message="投票结束时间必须晚于开始时间",
                request_id=_make_request_id("req_ops_vc_400"),
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
                request_id=_make_request_id("req_ops_vc_409"),
            ).model_dump(),
        )

    candidates_data = [c.model_dump() for c in body.candidates]
    cycle = await repo.create_vote_cycle(
        chapter_id=body.chapter_id,
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        created_by="ops",  # TODO: 从 JWT 中提取 operator_id
        created_reason=body.reason,
        candidates_data=candidates_data,
    )

    # 重新加载以获取 candidates 关系
    loaded_cycle = await repo.get_cycle_by_id(cycle.vote_cycle_id)
    candidates_resp = [CandidateResponse.model_validate(c) for c in loaded_cycle.candidates]

    request_id = _make_request_id("req_ops_vc")
    return CreateVoteCycleResponse(
        vote_cycle_id=cycle.vote_cycle_id,
        chapter_id=cycle.chapter_id,
        status=cycle.status,
        starts_at=cycle.starts_at,
        ends_at=cycle.ends_at,
        candidates=candidates_resp,
        request_id=request_id,
        trace_id=x_trace_id,
    )


@ops_router.post(
    "/vote-cycles/{vote_cycle_id}/schedule",
    response_model=TransitionVoteCycleResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Vote cycle not found"},
        409: {"model": ErrorResponse, "description": "Invalid state transition"},
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
) -> TransitionVoteCycleResponse:
    repo = VoteRepository(db)

    cycle = await repo.get_cycle_by_id(vote_cycle_id)
    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="VOTE_CYCLE_NOT_FOUND",
                message="投票周期不存在",
                request_id=_make_request_id("req_ops_vc_schedule_404"),
            ).model_dump(),
        )

    if not VoteRepository.is_valid_transition(cycle.status, "scheduled"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                code="INVALID_VOTE_STATE",
                message=f"投票周期状态 {cycle.status} 不允许迁移到 scheduled",
                request_id=_make_request_id("req_ops_vc_schedule_409"),
            ).model_dump(),
        )

    updated_cycle = await repo.transition_cycle_status(vote_cycle_id, "scheduled")
    request_id = _make_request_id("req_ops_vc_schedule")
    return TransitionVoteCycleResponse(
        vote_cycle_id=updated_cycle.vote_cycle_id,
        status=updated_cycle.status,
        request_id=request_id,
        trace_id=x_trace_id,
    )


@ops_router.post(
    "/vote-cycles/{vote_cycle_id}/open",
    response_model=TransitionVoteCycleResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Vote cycle not found"},
        409: {"model": ErrorResponse, "description": "Invalid state transition"},
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
) -> TransitionVoteCycleResponse:
    repo = VoteRepository(db)

    cycle = await repo.get_cycle_by_id(vote_cycle_id)
    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="VOTE_CYCLE_NOT_FOUND",
                message="投票周期不存在",
                request_id=_make_request_id("req_ops_vc_open_404"),
            ).model_dump(),
        )

    if not VoteRepository.is_valid_transition(cycle.status, "open"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                code="INVALID_VOTE_STATE",
                message=f"投票周期状态 {cycle.status} 不允许迁移到 open",
                request_id=_make_request_id("req_ops_vc_open_409"),
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
                request_id=_make_request_id("req_ops_vc_open_409_conflict"),
            ).model_dump(),
        )

    updated_cycle = await repo.transition_cycle_status(vote_cycle_id, "open")
    request_id = _make_request_id("req_ops_vc_open")
    return TransitionVoteCycleResponse(
        vote_cycle_id=updated_cycle.vote_cycle_id,
        status=updated_cycle.status,
        request_id=request_id,
        trace_id=x_trace_id,
    )


@ops_router.post(
    "/vote-cycles/{vote_cycle_id}/close",
    response_model=TransitionVoteCycleResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Vote cycle not found"},
        409: {"model": ErrorResponse, "description": "Invalid state transition"},
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
) -> TransitionVoteCycleResponse:
    repo = VoteRepository(db)

    cycle = await repo.get_cycle_by_id(vote_cycle_id)
    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="VOTE_CYCLE_NOT_FOUND",
                message="投票周期不存在",
                request_id=_make_request_id("req_ops_vc_close_404"),
            ).model_dump(),
        )

    if not VoteRepository.is_valid_transition(cycle.status, "closed"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                code="INVALID_VOTE_STATE",
                message=f"投票周期状态 {cycle.status} 不允许迁移到 closed",
                request_id=_make_request_id("req_ops_vc_close_409"),
            ).model_dump(),
        )

    # 关闭投票时自动计票
    tally_result = await repo.tally_votes(vote_cycle_id)
    winning_candidate_id = tally_result["winning_candidate_id"]

    updated_cycle = await repo.transition_cycle_status(vote_cycle_id, "closed")
    if winning_candidate_id is not None:
        updated_cycle.winning_candidate_id = winning_candidate_id

    request_id = _make_request_id("req_ops_vc_close")
    return TransitionVoteCycleResponse(
        vote_cycle_id=updated_cycle.vote_cycle_id,
        status=updated_cycle.status,
        winning_candidate_id=winning_candidate_id,
        request_id=request_id,
        trace_id=x_trace_id,
    )


@ops_router.post(
    "/vote-cycles/{vote_cycle_id}/finalize",
    response_model=TransitionVoteCycleResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Vote cycle not found"},
        409: {"model": ErrorResponse, "description": "Invalid state transition"},
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
) -> TransitionVoteCycleResponse:
    repo = VoteRepository(db)

    cycle = await repo.get_cycle_by_id(vote_cycle_id)
    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="VOTE_CYCLE_NOT_FOUND",
                message="投票周期不存在",
                request_id=_make_request_id("req_ops_vc_finalize_404"),
            ).model_dump(),
        )

    if not VoteRepository.is_valid_transition(cycle.status, "finalized"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                code="INVALID_VOTE_STATE",
                message=f"投票周期状态 {cycle.status} 不允许迁移到 finalized",
                request_id=_make_request_id("req_ops_vc_finalize_409"),
            ).model_dump(),
        )

    updated_cycle = await repo.transition_cycle_status(vote_cycle_id, "finalized")
    updated_cycle.finalized_at = datetime.now(timezone.utc)

    request_id = _make_request_id("req_ops_vc_finalize")
    return TransitionVoteCycleResponse(
        vote_cycle_id=updated_cycle.vote_cycle_id,
        status=updated_cycle.status,
        winning_candidate_id=updated_cycle.winning_candidate_id,
        request_id=request_id,
        trace_id=x_trace_id,
    )
