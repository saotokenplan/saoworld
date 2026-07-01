import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.repositories.vote_repo import VoteRepository
from app.schemas.vote import (
    CandidateInput,
    CandidateResponse,
    CreateVoteCycleRequest,
    CurrentVoteData,
    EnvelopeResponse,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    PaginationMeta,
    VoteCycleData,
    VoteHistoryData,
    VoteHistoryItem,
    VoteSubmitData,
    VoteSubmitRequest,
)

router = APIRouter()
ops_router = APIRouter()


def _make_request_id() -> str:
    return f"req_{uuid.uuid4().hex[:12]}"


def _get_trace_id(request: Request) -> str | None:
    return request.headers.get("X-Trace-Id")


# --- 健康检查 ---


@router.get("/health", tags=["health"])
async def health_check() -> HealthResponse:
    from app.core.config import settings

    return HealthResponse(
        service=settings.app_name,
        version=settings.app_version,
    )


# --- 玩家接口 ---


@router.get(
    "/votes/current",
    responses={
        404: {"description": "No open vote cycle"},
    },
    tags=["votes"],
)
async def get_current_vote(
    request: Request,
    x_player_id: str | None = Header(default=None, alias="X-Player-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse:
    repo = VoteRepository(db)
    cycle = await repo.get_current_open_cycle()

    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="NO_OPEN_VOTE_CYCLE",
                message="当前没有开放的投票周期",
                request_id=_make_request_id(),
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

    data = CurrentVoteData(
        vote_cycle_id=cycle.vote_cycle_id,
        chapter_id=cycle.chapter_id,
        status=cycle.status,
        starts_at=cycle.starts_at,
        ends_at=cycle.ends_at,
        candidates=candidate_responses,
        has_voted=has_voted,
        my_vote_candidate_id=my_vote_candidate_id,
    )

    return EnvelopeResponse(
        request_id=_make_request_id(),
        data=data.model_dump(),
        trace_id=_get_trace_id(request),
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
    x_player_id: str = Header(..., alias="X-Player-Id"),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse:
    try:
        player_uuid = uuid.UUID(x_player_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code="INVALID_PLAYER_ID",
                message="无效的玩家ID格式",
                request_id=_make_request_id(),
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
    trace_id = x_trace_id

    existing_by_key = await repo.vote_exists_by_idempotency_key(idempotency_key)
    if existing_by_key is not None:
        data = VoteSubmitData(
            vote_id=existing_by_key.vote_id,
            vote_cycle_id=existing_by_key.vote_cycle_id,
            candidate_id=existing_by_key.candidate_id,
            submitted_at=existing_by_key.created_at,
        )
        return EnvelopeResponse(
            request_id=_make_request_id(),
            data=data.model_dump(),
            trace_id=trace_id,
        )

    cycle = await repo.get_current_open_cycle()
    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                code="INVALID_VOTE_STATE",
                message="当前投票周期不可投票",
                request_id=_make_request_id(),
            ).model_dump(),
        )

    candidate = await repo.get_candidate_by_id(body.candidate_id)
    if candidate is None or candidate.vote_cycle_id != cycle.vote_cycle_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="CANDIDATE_NOT_FOUND",
                message="候选项不存在或不属于当前投票周期",
                request_id=_make_request_id(),
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
                request_id=_make_request_id(),
            ).model_dump(),
        )

    existing_vote = await repo.has_player_voted(cycle.vote_cycle_id, player_uuid)
    if existing_vote is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                code="ALREADY_VOTED",
                message="你已经在本周期投过票",
                request_id=_make_request_id(),
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

    data = VoteSubmitData(
        vote_id=vote.vote_id,
        vote_cycle_id=vote.vote_cycle_id,
        candidate_id=vote.candidate_id,
        submitted_at=vote.created_at or datetime.now(timezone.utc),
    )

    return EnvelopeResponse(
        request_id=_make_request_id(),
        data=data.model_dump(),
        trace_id=trace_id,
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
    x_player_id: str = Header(..., alias="X-Player-Id"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse:
    try:
        player_uuid = uuid.UUID(x_player_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code="INVALID_PLAYER_ID",
                message="无效的玩家ID格式",
                request_id=_make_request_id(),
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

    data = VoteHistoryData(
        player_id=player_uuid,
        votes=vote_items,
    )

    meta = PaginationMeta(total=total, limit=limit, offset=offset)

    return EnvelopeResponse(
        request_id=_make_request_id(),
        data=data.model_dump(),
        meta=meta.model_dump(),
        trace_id=_get_trace_id(request),
    )


# --- 运营接口 ---


@ops_router.post(
    "/vote-cycles",
    status_code=status.HTTP_201_CREATED,
    responses={
        422: {"description": "Validation error"},
    },
    tags=["ops"],
)
async def create_vote_cycle(
    body: CreateVoteCycleRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse:
    candidates_data = [c.model_dump() for c in body.candidates]

    repo = VoteRepository(db)
    cycle = await repo.create_vote_cycle(
        chapter_id=body.chapter_id,
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        created_by=body.created_by,
        created_reason=body.created_reason,
        candidates_data=candidates_data,
    )

    candidate_responses = [CandidateResponse.model_validate(c) for c in cycle.candidates]

    data = VoteCycleData(
        vote_cycle_id=cycle.vote_cycle_id,
        chapter_id=cycle.chapter_id,
        status=cycle.status,
        starts_at=cycle.starts_at,
        ends_at=cycle.ends_at,
        candidates=candidate_responses,
    )

    return EnvelopeResponse(
        request_id=_make_request_id(),
        data=data.model_dump(),
        trace_id=x_trace_id,
    )
