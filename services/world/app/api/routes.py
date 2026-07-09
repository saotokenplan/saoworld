import uuid

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import RequireOpsRole, RequireWorldReadScope, UserPayload
from app.core.errors import WorldErrorCodes, raise_world_error
from app.core.metrics import (
    record_npc_create,
    record_quest_create,
    record_region_create,
    record_region_status_transition,
)
from app.repositories.audit_repo import (
    ACTION_NPC_CREATE,
    ACTION_QUEST_CREATE,
    ACTION_REGION_CREATE,
    ACTION_REGION_STATUS_UPDATE,
    RESOURCE_NPC,
    RESOURCE_QUEST,
    RESOURCE_REGION,
    AuditRepository,
)
from app.repositories.world_repo import NpcRepository, QuestDefinitionRepository, WorldRepository
from app.schemas.world import (
    CreateNpcRequest,
    CreateNpcResponse,
    CreateQuestRequest,
    CreateQuestResponse,
    CreateRegionRequest,
    CreateRegionResponse,
    CreateWorldSkeletonRequest,
    CreateWorldSkeletonResponse,
    EnvelopeResponse,
    ErrorDetail,
    HealthResponse,
    NpcListResponse,
    NpcResponse,
    PaginatedMeta,
    QuestListResponse,
    QuestResponse,
    QuestType,
    RegionListResponse,
    RegionResponse,
    RegionStatus,
    UpdateRegionStatusRequest,
    UpdateRegionStatusResponse,
    WorldSkeletonResponse,
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


@router.get(
    "/world/skeleton",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "World skeleton not found"},
    },
    tags=["world"],
)
async def get_world_skeleton(
    request: Request,
    current_user: UserPayload = RequireWorldReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[WorldSkeletonResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_world_skeleton")

    repo = WorldRepository(db)
    skeleton = await repo.get_current_skeleton()

    if skeleton is None:
        raise_world_error(
            WorldErrorCodes.SKELETON_NOT_FOUND,
            "当前没有活跃的世界骨架快照",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=WorldSkeletonResponse(
            skeleton_id=skeleton.skeleton_id,
            world_version=skeleton.world_version,
            chapter_id=skeleton.chapter_id,
            regions=skeleton.regions,
            factions=skeleton.factions,
            reserved_characters=skeleton.reserved_characters,
            forbidden_tags=skeleton.forbidden_tags,
            reward_limits=skeleton.reward_limits,
            is_active=skeleton.is_active,
            created_at=skeleton.created_at,
            updated_at=skeleton.updated_at,
        ),
        trace_id=trace_id,
    )


ACTION_SKELETON_CREATE = "skeleton_create"
RESOURCE_SKELETON = "skeleton"


@ops_router.post(
    "/world/skeleton",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        409: {"description": "Version already exists"},
    },
    tags=["ops"],
)
async def create_world_skeleton(
    body: CreateWorldSkeletonRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[CreateWorldSkeletonResponse]:
    request_id = _make_request_id("req_ops_skeleton")

    repo = WorldRepository(db)

    existing = await repo.get_skeleton_by_version(body.world_version)
    if existing is not None:
        raise_world_error(
            WorldErrorCodes.SKELETON_VERSION_EXISTS,
            f"世界版本 {body.world_version} 已存在",
            request_id=request_id,
            status_code=status.HTTP_409_CONFLICT,
            details=[
                ErrorDetail(
                    location="body",
                    field="world_version",
                    issue="already_exists",
                    rejected_value=body.world_version,
                )
            ],
        )

    skeleton = await repo.create_skeleton(
        world_version=body.world_version,
        chapter_id=body.chapter_id,
        regions=body.regions,
        factions=body.factions,
        reserved_characters=body.reserved_characters,
        forbidden_tags=body.forbidden_tags,
        reward_limits=body.reward_limits,
        is_active=body.is_active,
    )

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_SKELETON_CREATE,
        resource_type=RESOURCE_SKELETON,
        resource_id=skeleton.skeleton_id,
        request_payload_jsonb=body.model_dump(mode="json"),
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=CreateWorldSkeletonResponse(
            skeleton_id=skeleton.skeleton_id,
            world_version=skeleton.world_version,
            chapter_id=skeleton.chapter_id,
            is_active=skeleton.is_active,
            request_id=request_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )


# ============================================================
# NPC 接口
# ============================================================


@router.get(
    "/world/npcs",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["world"],
)
async def list_npcs(
    request: Request,
    chapter_id: str | None = Query(default=None, max_length=64),
    faction_key: str | None = Query(default=None, max_length=128),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireWorldReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[NpcListResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_world_npcs")

    repo = NpcRepository(db)
    npcs, total = await repo.list_npcs(
        chapter_id=chapter_id,
        faction_key=faction_key,
        limit=limit,
        offset=offset,
    )

    npc_responses = [
        NpcResponse(
            npc_id=n.npc_id,
            npc_key=n.npc_key,
            chapter_id=n.chapter_id,
            name=n.name,
            title=n.title,
            faction_key=n.faction_key,
            role=n.role,
            location_key=n.location_key,
            description=n.description,
            personality=n.personality,
            dialogues=n.dialogues,
            related_quests=n.related_quests,
            rewards=n.rewards,
            created_at=n.created_at,
            updated_at=n.updated_at,
        )
        for n in npcs
    ]

    return EnvelopeResponse(
        request_id=request_id,
        data=NpcListResponse(npcs=npc_responses, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/world/npcs/{npc_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "NPC not found"},
    },
    tags=["world"],
)
async def get_npc_detail(
    npc_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireWorldReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[NpcResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_world_npc_detail")

    repo = NpcRepository(db)
    npc = await repo.get_npc_by_id(npc_id)

    if npc is None:
        raise_world_error(
            WorldErrorCodes.NPC_NOT_FOUND,
            "NPC 不存在",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="path",
                    field="npc_id",
                    issue="not_found",
                    rejected_value=str(npc_id),
                )
            ],
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=NpcResponse(
            npc_id=npc.npc_id,
            npc_key=npc.npc_key,
            chapter_id=npc.chapter_id,
            name=npc.name,
            title=npc.title,
            faction_key=npc.faction_key,
            role=npc.role,
            location_key=npc.location_key,
            description=npc.description,
            personality=npc.personality,
            dialogues=npc.dialogues,
            related_quests=npc.related_quests,
            rewards=npc.rewards,
            created_at=npc.created_at,
            updated_at=npc.updated_at,
        ),
        trace_id=trace_id,
    )


@router.get(
    "/world/npcs/by-key/{npc_key}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "NPC not found"},
    },
    tags=["world"],
)
async def get_npc_by_key(
    npc_key: str,
    request: Request,
    chapter_id: str | None = Query(default=None, max_length=64),
    current_user: UserPayload = RequireWorldReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[NpcResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_world_npc_by_key")

    if not npc_key or len(npc_key) > 128:
        raise_world_error(
            WorldErrorCodes.INVALID_NPC_KEY,
            "npc_key 长度必须在 1-128 之间",
            request_id=request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=[
                ErrorDetail(
                    location="path",
                    field="npc_key",
                    issue="invalid_length",
                    rejected_value=npc_key,
                )
            ],
        )

    repo = NpcRepository(db)
    if chapter_id:
        npc = await repo.get_npc_by_key_for_chapter(npc_key, chapter_id)
    else:
        npc = await repo.get_npc_by_key(npc_key)

    if npc is None:
        raise_world_error(
            WorldErrorCodes.NPC_NOT_FOUND,
            "NPC 不存在",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="path",
                    field="npc_key",
                    issue="not_found",
                    rejected_value=npc_key,
                )
            ],
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=NpcResponse(
            npc_id=npc.npc_id,
            npc_key=npc.npc_key,
            chapter_id=npc.chapter_id,
            name=npc.name,
            title=npc.title,
            faction_key=npc.faction_key,
            role=npc.role,
            location_key=npc.location_key,
            description=npc.description,
            personality=npc.personality,
            dialogues=npc.dialogues,
            related_quests=npc.related_quests,
            rewards=npc.rewards,
            created_at=npc.created_at,
            updated_at=npc.updated_at,
        ),
        trace_id=trace_id,
    )


@ops_router.post(
    "/world/npcs",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        409: {"description": "npc_key already exists"},
    },
    tags=["ops"],
)
async def create_npc(
    body: CreateNpcRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[CreateNpcResponse]:
    request_id = _make_request_id("req_ops_npc")

    repo = NpcRepository(db)
    existing = await repo.get_npc_by_key(body.npc_key)
    if existing is not None:
        raise_world_error(
            WorldErrorCodes.NPC_KEY_EXISTS,
            f"npc_key {body.npc_key} 已存在",
            request_id=request_id,
            status_code=status.HTTP_409_CONFLICT,
            details=[
                ErrorDetail(
                    location="body",
                    field="npc_key",
                    issue="already_exists",
                    rejected_value=body.npc_key,
                )
            ],
        )

    npc = await repo.create_npc(
        npc_key=body.npc_key,
        chapter_id=body.chapter_id,
        name=body.name,
        title=body.title,
        faction_key=body.faction_key,
        role=body.role,
        location_key=body.location_key,
        description=body.description,
        personality=body.personality,
        dialogues=body.dialogues,
        related_quests=body.related_quests,
        rewards=body.rewards,
    )

    record_npc_create()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_NPC_CREATE,
        resource_type=RESOURCE_NPC,
        resource_id=npc.npc_id,
        request_payload_jsonb=body.model_dump(mode="json"),
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=CreateNpcResponse(
            npc_id=npc.npc_id,
            npc_key=npc.npc_key,
            chapter_id=npc.chapter_id,
            name=npc.name,
            request_id=request_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )


# ============================================================
# Quest 接口
# ============================================================


@router.get(
    "/world/quests",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["world"],
)
async def list_quests(
    request: Request,
    chapter_id: str | None = Query(default=None, max_length=64),
    quest_type: QuestType | None = Query(default=None),
    region_key: str | None = Query(default=None, max_length=128),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireWorldReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[QuestListResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_world_quests")

    repo = QuestDefinitionRepository(db)
    quests, total = await repo.list_quests(
        chapter_id=chapter_id,
        quest_type=quest_type.value if quest_type else None,
        region_key=region_key,
        limit=limit,
        offset=offset,
    )

    quest_responses = [
        QuestResponse(
            quest_id=q.quest_id,
            quest_key=q.quest_key,
            chapter_id=q.chapter_id,
            title=q.title,
            description=q.description,
            quest_type=QuestType(q.quest_type),
            region_key=q.region_key,
            start_npc_key=q.start_npc_key,
            end_npc_key=q.end_npc_key,
            prerequisites=q.prerequisites,
            objectives=q.objectives,
            rewards=q.rewards,
            failure_condition=q.failure_condition,
            created_at=q.created_at,
            updated_at=q.updated_at,
        )
        for q in quests
    ]

    return EnvelopeResponse(
        request_id=request_id,
        data=QuestListResponse(quests=quest_responses, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/world/quests/{quest_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Quest not found"},
    },
    tags=["world"],
)
async def get_quest_detail(
    quest_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireWorldReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[QuestResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_world_quest_detail")

    repo = QuestDefinitionRepository(db)
    quest = await repo.get_quest_by_id(quest_id)

    if quest is None:
        raise_world_error(
            WorldErrorCodes.QUEST_NOT_FOUND,
            "任务不存在",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="path",
                    field="quest_id",
                    issue="not_found",
                    rejected_value=str(quest_id),
                )
            ],
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=QuestResponse(
            quest_id=quest.quest_id,
            quest_key=quest.quest_key,
            chapter_id=quest.chapter_id,
            title=quest.title,
            description=quest.description,
            quest_type=QuestType(quest.quest_type),
            region_key=quest.region_key,
            start_npc_key=quest.start_npc_key,
            end_npc_key=quest.end_npc_key,
            prerequisites=quest.prerequisites,
            objectives=quest.objectives,
            rewards=quest.rewards,
            failure_condition=quest.failure_condition,
            created_at=quest.created_at,
            updated_at=quest.updated_at,
        ),
        trace_id=trace_id,
    )


@router.get(
    "/world/quests/by-key/{quest_key}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Quest not found"},
    },
    tags=["world"],
)
async def get_quest_by_key(
    quest_key: str,
    request: Request,
    chapter_id: str | None = Query(default=None, max_length=64),
    current_user: UserPayload = RequireWorldReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[QuestResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_world_quest_by_key")

    if not quest_key or len(quest_key) > 128:
        raise_world_error(
            WorldErrorCodes.INVALID_QUEST_KEY,
            "quest_key 长度必须在 1-128 之间",
            request_id=request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=[
                ErrorDetail(
                    location="path",
                    field="quest_key",
                    issue="invalid_length",
                    rejected_value=quest_key,
                )
            ],
        )

    repo = QuestDefinitionRepository(db)
    if chapter_id:
        quest = await repo.get_quest_by_key_for_chapter(quest_key, chapter_id)
    else:
        quest = await repo.get_quest_by_key(quest_key)

    if quest is None:
        raise_world_error(
            WorldErrorCodes.QUEST_NOT_FOUND,
            "任务不存在",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="path",
                    field="quest_key",
                    issue="not_found",
                    rejected_value=quest_key,
                )
            ],
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=QuestResponse(
            quest_id=quest.quest_id,
            quest_key=quest.quest_key,
            chapter_id=quest.chapter_id,
            title=quest.title,
            description=quest.description,
            quest_type=QuestType(quest.quest_type),
            region_key=quest.region_key,
            start_npc_key=quest.start_npc_key,
            end_npc_key=quest.end_npc_key,
            prerequisites=quest.prerequisites,
            objectives=quest.objectives,
            rewards=quest.rewards,
            failure_condition=quest.failure_condition,
            created_at=quest.created_at,
            updated_at=quest.updated_at,
        ),
        trace_id=trace_id,
    )


@ops_router.post(
    "/world/quests",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        409: {"description": "quest_key already exists"},
    },
    tags=["ops"],
)
async def create_quest(
    body: CreateQuestRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[CreateQuestResponse]:
    request_id = _make_request_id("req_ops_quest")

    repo = QuestDefinitionRepository(db)
    existing = await repo.get_quest_by_key(body.quest_key)
    if existing is not None:
        raise_world_error(
            WorldErrorCodes.QUEST_KEY_EXISTS,
            f"quest_key {body.quest_key} 已存在",
            request_id=request_id,
            status_code=status.HTTP_409_CONFLICT,
            details=[
                ErrorDetail(
                    location="body",
                    field="quest_key",
                    issue="already_exists",
                    rejected_value=body.quest_key,
                )
            ],
        )

    quest = await repo.create_quest(
        quest_key=body.quest_key,
        chapter_id=body.chapter_id,
        title=body.title,
        description=body.description,
        quest_type=body.quest_type.value,
        region_key=body.region_key,
        start_npc_key=body.start_npc_key,
        end_npc_key=body.end_npc_key,
        prerequisites=body.prerequisites,
        objectives=body.objectives,
        rewards=body.rewards,
        failure_condition=body.failure_condition,
    )

    record_quest_create()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_QUEST_CREATE,
        resource_type=RESOURCE_QUEST,
        resource_id=quest.quest_id,
        request_payload_jsonb=body.model_dump(mode="json"),
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=CreateQuestResponse(
            quest_id=quest.quest_id,
            quest_key=quest.quest_key,
            chapter_id=quest.chapter_id,
            title=quest.title,
            quest_type=QuestType(quest.quest_type),
            request_id=request_id,
            trace_id=x_trace_id,
        ),
        trace_id=x_trace_id,
    )
