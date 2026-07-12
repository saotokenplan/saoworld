import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.contribution import (
    calculate_vote_weight_multiplier,
    check_vote_eligibility,
)
from app.core.db import get_db
from app.core.deps import (
    RequireOpsScope,
    RequireVotesHistoryReadScope,
    RequireVotesReadScope,
    RequireVotesSubmitScope,
    UserPayload,
)
from app.core.errors import VoteErrorCodes, raise_vote_error
from app.core.event_publisher import event_publisher
from app.core.metrics import (
    record_vote_cycle_transition,
    record_vote_eligibility_rejected,
    record_vote_submission,
)
from app.core.player_client import PlayerContributionClient
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
    HealthResponse,
    PaginatedMeta,
    TransitionVoteCycleRequest,
    TransitionVoteCycleResponse,
    VoteCycleStatus,
    VoteHistoryItem,
    VoteHistoryResponse,
    VoteSubmitRequest,
    VoteSubmitResponse,
)

router = APIRouter()
ops_router = APIRouter()

logger = structlog.get_logger()


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
        raise_vote_error(
            VoteErrorCodes.NO_OPEN_VOTE_CYCLE,
            "当前没有开放的投票周期",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
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
            status=VoteCycleStatus(cycle.status),
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
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[VoteSubmitResponse]:
    request_id = _make_request_id("req_vote_submit")

    # 优先使用 JWT 中的 user_id，兼容 X-Player-Id
    player_id_str = current_user.user_id

    try:
        player_uuid = uuid.UUID(player_id_str)
    except ValueError:
        raise_vote_error(
            VoteErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id=request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=[
                ErrorDetail(
                    location="token",
                    field="sub",
                    issue="invalid_uuid",
                    rejected_value=player_id_str,
                )
            ],
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
                weight=existing_by_key.weight,
                request_id=request_id,
                trace_id=x_trace_id,
            ),
            trace_id=x_trace_id,
        )

    cycle = await repo.get_current_open_cycle()
    if cycle is None:
        raise_vote_error(
            VoteErrorCodes.INVALID_VOTE_STATE,
            "当前投票周期不可投票",
            request_id=request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    candidate = await repo.get_candidate_by_id(body.candidate_id)
    if candidate is None or candidate.vote_cycle_id != cycle.vote_cycle_id:
        raise_vote_error(
            VoteErrorCodes.CANDIDATE_NOT_FOUND,
            "候选项不存在或不属于当前投票周期",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="body",
                    field="candidate_id",
                    issue="not_found",
                    rejected_value=str(body.candidate_id),
                )
            ],
        )

    if candidate.status != "active":
        raise_vote_error(
            VoteErrorCodes.CANDIDATE_NOT_ACTIVE,
            "该候选项当前不可投票",
            request_id=request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    existing_vote = await repo.has_player_voted(cycle.vote_cycle_id, player_uuid)
    if existing_vote is not None:
        raise_vote_error(
            VoteErrorCodes.ALREADY_VOTED,
            "你已经在本周期投过票",
            request_id=request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    # 查询玩家贡献度并校验投票资格
    contribution_client = PlayerContributionClient()
    try:
        contribution_points = await contribution_client.get_contribution(
            player_id=str(player_uuid),
            authorization=authorization,
        )
    finally:
        await contribution_client.close()

    if not check_vote_eligibility(contribution_points, settings.contribution_threshold):
        record_vote_eligibility_rejected(player_id=str(player_uuid))
        raise_vote_error(
            VoteErrorCodes.INSUFFICIENT_CONTRIBUTION,
            f"贡献度不足，当前贡献度 {contribution_points}，投票资格门槛为 {settings.contribution_threshold}",
            request_id=request_id,
            status_code=status.HTTP_403_FORBIDDEN,
            details=[
                ErrorDetail(
                    location="player",
                    field="contribution_points",
                    issue="below_threshold",
                    rejected_value=contribution_points,
                )
            ],
        )

    # 根据贡献度计算投票权重倍率
    weight_multiplier = calculate_vote_weight_multiplier(contribution_points)
    final_weight = round(body.weight * weight_multiplier, 2)

    vote = await repo.create_vote(
        vote_cycle_id=cycle.vote_cycle_id,
        player_id=player_uuid,
        candidate_id=body.candidate_id,
        weight=final_weight,
        device_fingerprint_hash=body.device_fingerprint_hash,
        idempotency_key=idempotency_key,
    )

    # 业务指标：投票提交计数
    record_vote_submission()

    # 审计日志：投票提交
    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=str(player_uuid),
        operator_role="player",
        action=ACTION_VOTE_SUBMIT,
        resource_type=RESOURCE_VOTE,
        resource_id=vote.vote_id,
        request_payload_jsonb={
            "candidate_id": str(body.candidate_id),
            "weight": body.weight,
            "final_weight": final_weight,
            "weight_multiplier": weight_multiplier,
            "contribution_points": contribution_points,
        },
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=VoteSubmitResponse(
            vote_id=vote.vote_id,
            vote_cycle_id=vote.vote_cycle_id,
            candidate_id=vote.candidate_id,
            submitted_at=vote.created_at or datetime.now(timezone.utc),
            weight=final_weight,
            weight_multiplier=weight_multiplier,
            contribution_points=contribution_points,
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
    authorization: str | None = Header(default=None, alias="Authorization"),
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
        raise_vote_error(
            VoteErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id=request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=[
                ErrorDetail(
                    location="token",
                    field="sub",
                    issue="invalid_uuid",
                    rejected_value=player_id_str,
                )
            ],
        )

    repo = VoteRepository(db)
    rows, total = await repo.get_vote_history(player_uuid, limit=limit, offset=offset)

    # 收集所有投票周期 ID，批量查询内容包信息
    vote_cycle_ids = [v.vote_cycle_id for v, _ in rows]

    content_package_map: dict[uuid.UUID, Any] = {}
    if vote_cycle_ids:
        try:
            from app.core.content_client import ContentPackageClient

            content_client = ContentPackageClient()
            content_package_map = await content_client.get_content_packages_batch(
                vote_cycle_ids,
                authorization=authorization,
            )
        except Exception as exc:
            logger.error(
                "content_package_batch_query_failed",
                error=str(exc),
                vote_cycle_ids=[str(vcid) for vcid in vote_cycle_ids],
            )
        finally:
            await content_client.close()

    vote_items = []
    for v, c in rows:
        # 查找对应的内容包信息
        content_package_info = content_package_map.get(v.vote_cycle_id)

        content_package_data = None
        if content_package_info:
            content_package_data = {
                "content_package_id": content_package_info.content_package_id,
                "version": content_package_info.version,
                "status": content_package_info.status,
                "affected_regions": content_package_info.affected_regions,
                "landed_at": content_package_info.landed_at,
            }

        vote_items.append(
            VoteHistoryItem(
                vote_id=v.vote_id,
                vote_cycle_id=v.vote_cycle_id,
                candidate_id=v.candidate_id,
                candidate_title=c.title,
                weight=v.weight,
                created_at=v.created_at,
                content_package=content_package_data,
            )
        )

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
        raise_vote_error(
            VoteErrorCodes.INVALID_ARGUMENT,
            "投票结束时间必须晚于开始时间",
            request_id=request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=[
                ErrorDetail(
                    location="body",
                    field="ends_at",
                    issue="must_be_after_starts_at",
                    rejected_value=body.ends_at.isoformat(),
                )
            ],
        )

    repo = VoteRepository(db)

    existing_open = await repo.get_open_cycle_for_chapter(body.chapter_id)
    if existing_open is not None:
        raise_vote_error(
            VoteErrorCodes.VOTE_CYCLE_CONFLICT,
            "当前章节已存在开放中的投票周期",
            request_id=request_id,
            status_code=status.HTTP_409_CONFLICT,
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

    loaded_cycle = await repo.get_cycle_by_id(cycle.vote_cycle_id)
    assert loaded_cycle is not None
    candidates_resp = [CandidateResponse.model_validate(c) for c in loaded_cycle.candidates]

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
            status=VoteCycleStatus(cycle.status),
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
        raise_vote_error(
            VoteErrorCodes.VOTE_CYCLE_NOT_FOUND,
            "投票周期不存在",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if not VoteRepository.is_valid_transition(cycle.status, "scheduled"):
        raise_vote_error(
            VoteErrorCodes.INVALID_VOTE_STATE,
            f"投票周期状态 {cycle.status} 不允许迁移到 scheduled",
            request_id=request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    from_status = cycle.status
    updated_cycle = await repo.transition_cycle_status(vote_cycle_id, "scheduled")
    assert updated_cycle is not None

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

    # 业务指标：状态迁移计数
    record_vote_cycle_transition(from_status, "scheduled")

    return EnvelopeResponse(
        request_id=request_id,
        data=TransitionVoteCycleResponse(
            vote_cycle_id=updated_cycle.vote_cycle_id,
            status=VoteCycleStatus(updated_cycle.status),
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
        raise_vote_error(
            VoteErrorCodes.VOTE_CYCLE_NOT_FOUND,
            "投票周期不存在",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if not VoteRepository.is_valid_transition(cycle.status, "open"):
        raise_vote_error(
            VoteErrorCodes.INVALID_VOTE_STATE,
            f"投票周期状态 {cycle.status} 不允许迁移到 open",
            request_id=request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    # 检查同一章节是否已有开放周期
    existing_open = await repo.get_open_cycle_for_chapter(cycle.chapter_id)
    if existing_open is not None and existing_open.vote_cycle_id != vote_cycle_id:
        raise_vote_error(
            VoteErrorCodes.VOTE_CYCLE_CONFLICT,
            "当前章节已存在开放中的投票周期",
            request_id=request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    from_status = cycle.status
    updated_cycle = await repo.transition_cycle_status(vote_cycle_id, "open")
    assert updated_cycle is not None

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

    # 业务指标：状态迁移计数
    record_vote_cycle_transition(from_status, "open")

    return EnvelopeResponse(
        request_id=request_id,
        data=TransitionVoteCycleResponse(
            vote_cycle_id=updated_cycle.vote_cycle_id,
            status=VoteCycleStatus(updated_cycle.status),
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
        raise_vote_error(
            VoteErrorCodes.VOTE_CYCLE_NOT_FOUND,
            "投票周期不存在",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if not VoteRepository.is_valid_transition(cycle.status, "closed"):
        raise_vote_error(
            VoteErrorCodes.INVALID_VOTE_STATE,
            f"投票周期状态 {cycle.status} 不允许迁移到 closed",
            request_id=request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    # 关闭投票时自动计票
    tally_result = await repo.tally_votes(vote_cycle_id)
    winning_candidate_id = tally_result["winning_candidate_id"]

    from_status = cycle.status
    updated_cycle = await repo.transition_cycle_status(vote_cycle_id, "closed")
    assert updated_cycle is not None
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

    # 业务指标：状态迁移计数
    record_vote_cycle_transition(from_status, "closed")

    # 事件发布：投票周期关闭
    try:
        await event_publisher.publish_vote_cycle_closed(
            vote_cycle_id=str(vote_cycle_id),
            chapter_id=cycle.chapter_id,
            closed_at=updated_cycle.updated_at.isoformat() if updated_cycle.updated_at else datetime.now(timezone.utc).isoformat(),
            trace_id=x_trace_id or "",
        )
    except Exception as exc:
        logger.error("event_publish_failed", event_type="vote_cycle_closed", vote_cycle_id=str(vote_cycle_id), error=str(exc))

    return EnvelopeResponse(
        request_id=request_id,
        data=TransitionVoteCycleResponse(
            vote_cycle_id=updated_cycle.vote_cycle_id,
            status=VoteCycleStatus(updated_cycle.status),
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
        raise_vote_error(
            VoteErrorCodes.VOTE_CYCLE_NOT_FOUND,
            "投票周期不存在",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if not VoteRepository.is_valid_transition(cycle.status, "finalized"):
        raise_vote_error(
            VoteErrorCodes.INVALID_VOTE_STATE,
            f"投票周期状态 {cycle.status} 不允许迁移到 finalized",
            request_id=request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    from_status = cycle.status
    updated_cycle = await repo.transition_cycle_status(vote_cycle_id, "finalized")
    assert updated_cycle is not None
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

    # 业务指标：状态迁移计数
    record_vote_cycle_transition(from_status, "finalized")

    # 事件发布：投票结果结算完成
    try:
        winning_candidate_name = ""
        total_votes = 0
        generated_params = None
        region_scope = None
        if updated_cycle.winning_candidate_id is not None:
            candidates = await repo.get_candidates_for_cycle(vote_cycle_id)
            for c in candidates:
                if c.candidate_id == updated_cycle.winning_candidate_id:
                    winning_candidate_name = c.title
                    generated_params = c.generated_params
                    region_scope = c.region_scope
                    break
            tally_result = await repo.tally_votes(vote_cycle_id)
            total_votes = tally_result.get("total_votes", 0)
        await event_publisher.publish_vote_result_finalized(
            vote_cycle_id=str(vote_cycle_id),
            chapter_id=cycle.chapter_id,
            winning_candidate_id=str(updated_cycle.winning_candidate_id) if updated_cycle.winning_candidate_id else "",
            winning_candidate_name=winning_candidate_name,
            total_votes=total_votes,
            finalized_at=updated_cycle.finalized_at.isoformat() if updated_cycle.finalized_at else datetime.now(timezone.utc).isoformat(),
            generated_params=generated_params,
            region_scope=region_scope,
            trace_id=x_trace_id or "",
        )
    except Exception as exc:
        logger.error("event_publish_failed", event_type="vote_result_finalized", vote_cycle_id=str(vote_cycle_id), error=str(exc))

    return EnvelopeResponse(
        request_id=request_id,
        data=TransitionVoteCycleResponse(
            vote_cycle_id=updated_cycle.vote_cycle_id,
            status=VoteCycleStatus(updated_cycle.status),
            winning_candidate_id=updated_cycle.winning_candidate_id,
            request_id=request_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )
