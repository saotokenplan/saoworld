import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    RequireOpsRole,
    RequirePlayerRole,
    RequireQuestsReadScope,
    UserPayload,
)
from app.core.metrics import (
    record_player_create,
    record_player_region_unlock,
    record_player_update,
)
from app.repositories.audit_repo import (
    ACTION_PLAYER_CREATE,
    ACTION_PLAYER_UPDATE,
    ACTION_REGION_UNLOCK,
    RESOURCE_PLAYER,
    RESOURCE_REGION,
    AuditRepository,
)
from app.repositories.player_quest_repo import PlayerQuestRepository
from app.repositories.player_region_repo import PlayerRegionRepository
from app.repositories.player_repo import PlayerRepository
from app.schemas.player import (
    CreatePlayerRequest,
    EnvelopeResponse,
    ErrorResponse,
    HealthResponse,
    PaginatedMeta,
    PlayerQuestResponse,
    PlayerRegionResponse,
    PlayerResponse,
    QuestStatus,
    UpdatePlayerRequest,
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
    "/player/info",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Player not found"},
    },
    tags=["player"],
)
async def get_player_info(
    request: Request,
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[PlayerResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_player_info")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code="INVALID_PLAYER_ID",
                message="无效的玩家ID格式",
                request_id=request_id,
            ).model_dump(),
        )

    repo = PlayerRepository(db)
    player = await repo.get_player_by_id(player_uuid)

    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="PLAYER_NOT_FOUND",
                message="玩家不存在",
                request_id=request_id,
            ).model_dump(),
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=PlayerResponse.model_validate(player),
        trace_id=trace_id,
    )


@router.get(
    "/player/quests",
    responses={
        401: {"description": "Unauthorized"},
        400: {"description": "Invalid player ID"},
    },
    tags=["player"],
)
async def get_player_quests(
    request: Request,
    current_user: UserPayload = RequireQuestsReadScope,
    quest_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[PlayerQuestResponse]]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_player_quests")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code="INVALID_PLAYER_ID",
                message="无效的玩家ID格式",
                request_id=request_id,
            ).model_dump(),
        )

    if quest_status is not None and quest_status not in [s.value for s in QuestStatus]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code="INVALID_QUEST_STATUS",
                message=f"无效的任务状态: {quest_status}",
                request_id=request_id,
            ).model_dump(),
        )

    repo = PlayerQuestRepository(db)
    quests, total = await repo.get_player_quests(
        player_uuid, status=quest_status, limit=limit, offset=offset
    )

    quest_responses = [PlayerQuestResponse.model_validate(q) for q in quests]

    return EnvelopeResponse(
        request_id=request_id,
        data=quest_responses,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/player/regions",
    responses={
        401: {"description": "Unauthorized"},
        400: {"description": "Invalid player ID"},
    },
    tags=["player"],
)
async def get_player_regions(
    request: Request,
    current_user: UserPayload = RequirePlayerRole,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[PlayerRegionResponse]]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_player_regions")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                code="INVALID_PLAYER_ID",
                message="无效的玩家ID格式",
                request_id=request_id,
            ).model_dump(),
        )

    repo = PlayerRegionRepository(db)
    regions, total = await repo.get_player_regions(player_uuid, limit=limit, offset=offset)

    region_responses = [PlayerRegionResponse.model_validate(r) for r in regions]

    return EnvelopeResponse(
        request_id=request_id,
        data=region_responses,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@ops_router.post(
    "/players",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["ops"],
)
async def create_player(
    body: CreatePlayerRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[PlayerResponse]:
    request_id = _make_request_id("req_ops_player_create")

    repo = PlayerRepository(db)
    player = await repo.create_player(body.display_name, body.chapter_id)

    record_player_create()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_PLAYER_CREATE,
        resource_type=RESOURCE_PLAYER,
        resource_id=player.player_id,
        request_payload_jsonb=body.model_dump(mode="json"),
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=PlayerResponse.model_validate(player),
        trace_id=x_trace_id,
    )


@ops_router.get(
    "/players",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["ops"],
)
async def list_players(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[list[PlayerResponse]]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_ops_players")

    repo = PlayerRepository(db)
    players, total = await repo.list_players(limit=limit, offset=offset)

    player_responses = [PlayerResponse.model_validate(p) for p in players]

    return EnvelopeResponse(
        request_id=request_id,
        data=player_responses,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@ops_router.get(
    "/players/{player_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Player not found"},
    },
    tags=["ops"],
)
async def get_player_detail(
    player_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[PlayerResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_ops_player_detail")

    repo = PlayerRepository(db)
    player = await repo.get_player_by_id(player_id)

    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="PLAYER_NOT_FOUND",
                message="玩家不存在",
                request_id=request_id,
            ).model_dump(),
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=PlayerResponse.model_validate(player),
        trace_id=trace_id,
    )


@ops_router.put(
    "/players/{player_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Player not found"},
    },
    tags=["ops"],
)
async def update_player(
    player_id: uuid.UUID,
    body: UpdatePlayerRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[PlayerResponse]:
    request_id = _make_request_id("req_ops_player_update")

    repo = PlayerRepository(db)
    player = await repo.update_player(
        player_id, display_name=body.display_name, chapter_id=body.chapter_id
    )

    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                code="PLAYER_NOT_FOUND",
                message="玩家不存在",
                request_id=request_id,
            ).model_dump(),
        )

    record_player_update()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_PLAYER_UPDATE,
        resource_type=RESOURCE_PLAYER,
        resource_id=player.player_id,
        request_payload_jsonb=body.model_dump(mode="json"),
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=PlayerResponse.model_validate(player),
        trace_id=x_trace_id,
    )


@ops_router.post(
    "/players/{player_id}/regions/{region_id}/unlock",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Player not found"},
    },
    tags=["ops"],
)
async def unlock_player_region(
    player_id: uuid.UUID,
    region_id: str,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[PlayerRegionResponse]:
    request_id = _make_request_id("req_ops_region_unlock")

    repo = PlayerRegionRepository(db)
    player_region = await repo.unlock_region(player_id, region_id)

    record_player_region_unlock()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_REGION_UNLOCK,
        resource_type=RESOURCE_REGION,
        resource_id=player_region.player_region_id,
        request_payload_jsonb={"player_id": str(player_id), "region_id": region_id},
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=PlayerRegionResponse.model_validate(player_region),
        trace_id=x_trace_id,
    )