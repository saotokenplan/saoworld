import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import RequireOpsRole, RequireWorldReadScope, UserPayload
from app.core.errors import WorldErrorCodes, raise_world_error
from app.core.metrics import (
    record_npc_create,
    record_quest_create,
    record_region_create,
    record_region_status_transition,
    record_item_create,
    record_item_update,
    record_item_delete,
    record_monster_create,
)
from app.repositories.audit_repo import (
    ACTION_NPC_CREATE,
    ACTION_QUEST_CREATE,
    ACTION_REGION_CREATE,
    ACTION_REGION_STATUS_UPDATE,
    ACTION_ITEM_CREATE,
    ACTION_ITEM_UPDATE,
    ACTION_ITEM_DELETE,
    ACTION_MONSTER_CREATE,
    RESOURCE_NPC,
    RESOURCE_QUEST,
    RESOURCE_REGION,
    RESOURCE_ITEM_DEFINITION,
    RESOURCE_MONSTER_DEFINITION,
    AuditRepository,
)
from app.repositories.world_repo import (
    ItemDefinitionRepository,
    MonsterDefinitionRepository,
    NpcRepository,
    QuestDefinitionRepository,
    WorldRepository,
)
from app.schemas.world import (
    BossListResponse,
    CreateBossRequest,
    CreateItemRequest,
    CreateItemResponse,
    CreateMonsterRequest,
    CreateMonsterResponse,
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
    ItemListResponse,
    ItemResponse,
    ItemRarity,
    ItemType,
    MonsterListResponse,
    MonsterResponse,
    MonsterType,
    NpcListResponse,
    NpcResponse,
    PaginatedMeta,
    QuestListResponse,
    QuestResponse,
    QuestType,
    RegionListResponse,
    RegionResponse,
    RegionStatus,
    UpdateItemRequest,
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
    player_reputation: int | None = Query(default=None, ge=0),
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
        player_reputation=player_reputation,
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
            min_reputation=n.min_reputation,
            interaction_restrictions=n.interaction_restrictions_jsonb,
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
            min_reputation=npc.min_reputation,
            interaction_restrictions=npc.interaction_restrictions_jsonb,
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
            min_reputation=npc.min_reputation,
            interaction_restrictions=npc.interaction_restrictions_jsonb,
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
        min_reputation=body.min_reputation,
        interaction_restrictions=body.interaction_restrictions,
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
    player_reputation: int | None = Query(default=None, ge=0),
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
        player_reputation=player_reputation,
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
            min_reputation=q.min_reputation,
            required_reputation_level=q.required_reputation_level,
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
            min_reputation=quest.min_reputation,
            required_reputation_level=quest.required_reputation_level,
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
            min_reputation=quest.min_reputation,
            required_reputation_level=quest.required_reputation_level,
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
        min_reputation=body.min_reputation,
        required_reputation_level=body.required_reputation_level,
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


# ============================================================
# Item 接口
# ============================================================


@router.get(
    "/world/items",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["world"],
)
async def list_items(
    request: Request,
    item_type: ItemType | None = Query(default=None),
    rarity: ItemRarity | None = Query(default=None),
    chapter_id: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireWorldReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[ItemListResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_world_items")

    repo = ItemDefinitionRepository(db)
    items, total = await repo.list_items(
        item_type=item_type.value if item_type else None,
        rarity=rarity.value if rarity else None,
        chapter_id=chapter_id,
        limit=limit,
        offset=offset,
    )

    item_responses = [ItemResponse.model_validate(item) for item in items]

    return EnvelopeResponse(
        request_id=request_id,
        data=ItemListResponse(items=item_responses, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/world/items/{item_key}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Item not found"},
    },
    tags=["world"],
)
async def get_item_detail(
    item_key: str,
    request: Request,
    current_user: UserPayload = RequireWorldReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[ItemResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_world_item_detail")

    if not item_key or len(item_key) > 128:
        raise_world_error(
            WorldErrorCodes.INVALID_ARGUMENT,
            "item_key 长度必须在 1-128 之间",
            request_id=request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=[
                ErrorDetail(
                    location="path",
                    field="item_key",
                    issue="invalid_length",
                    rejected_value=item_key,
                )
            ],
        )

    repo = ItemDefinitionRepository(db)
    item = await repo.get_item_by_key(item_key)

    if item is None:
        raise_world_error(
            WorldErrorCodes.ITEM_NOT_FOUND,
            "物品不存在",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="path",
                    field="item_key",
                    issue="not_found",
                    rejected_value=item_key,
                )
            ],
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=ItemResponse.model_validate(item),
        trace_id=trace_id,
    )


@ops_router.post(
    "/world/items",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        409: {"description": "item_key already exists"},
    },
    tags=["ops"],
)
async def create_item(
    body: CreateItemRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[ItemResponse]:
    request_id = _make_request_id("req_ops_item")

    repo = ItemDefinitionRepository(db)
    existing = await repo.get_item_by_key(body.item_key)
    if existing is not None:
        raise_world_error(
            WorldErrorCodes.ITEM_KEY_EXISTS,
            f"item_key {body.item_key} 已存在",
            request_id=request_id,
            status_code=status.HTTP_409_CONFLICT,
            details=[
                ErrorDetail(
                    location="body",
                    field="item_key",
                    issue="already_exists",
                    rejected_value=body.item_key,
                )
            ],
        )

    valid_equip_types = {"weapon", "armor", "accessory"}
    if body.item_type.value in valid_equip_types and body.item_slot is None:
        raise_world_error(
            WorldErrorCodes.INVALID_ITEM_SLOT,
            "装备类型物品必须指定装备槽位",
            request_id=request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=[
                ErrorDetail(
                    location="body",
                    field="item_slot",
                    issue="required_for_equipment",
                    rejected_value=None,
                )
            ],
        )

    if body.item_type.value not in valid_equip_types and body.item_slot is not None:
        raise_world_error(
            WorldErrorCodes.INVALID_ITEM_SLOT,
            "非装备类型物品不能有装备槽位",
            request_id=request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=[
                ErrorDetail(
                    location="body",
                    field="item_slot",
                    issue="not_allowed_for_non_equipment",
                    rejected_value=body.item_slot.value,
                )
            ],
        )

    item = await repo.create_item(
        item_key=body.item_key,
        item_type=body.item_type.value,
        item_slot=body.item_slot.value if body.item_slot else None,
        name=body.name,
        description=body.description,
        rarity=body.rarity.value,
        chapter_id=body.chapter_id,
        level_requirement=body.level_requirement,
        stats=body.stats,
        effects=body.effects,
        sell_price=body.sell_price,
        stackable=body.stackable,
    )

    record_item_create()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_ITEM_CREATE,
        resource_type=RESOURCE_ITEM_DEFINITION,
        resource_id=item.item_id,
        request_payload_jsonb=body.model_dump(mode="json"),
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=ItemResponse.model_validate(item),
        trace_id=x_trace_id,
    )


@ops_router.put(
    "/world/items/{item_id}",
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Item not found"},
    },
    tags=["ops"],
)
async def update_item(
    item_id: uuid.UUID,
    body: UpdateItemRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[ItemResponse]:
    request_id = _make_request_id("req_ops_item_update")

    repo = ItemDefinitionRepository(db)
    item = await repo.get_item_by_id(item_id)

    if item is None:
        raise_world_error(
            WorldErrorCodes.ITEM_NOT_FOUND,
            "物品不存在",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="path",
                    field="item_id",
                    issue="not_found",
                    rejected_value=str(item_id),
                )
            ],
        )

    update_data: dict[str, Any] = {}
    if body.name is not None:
        update_data["name"] = body.name
    if body.description is not None:
        update_data["description"] = body.description
    if body.rarity is not None:
        update_data["rarity"] = body.rarity.value
    if body.level_requirement is not None:
        update_data["level_requirement"] = body.level_requirement
    if body.stats is not None:
        update_data["stats_jsonb"] = body.stats
    if body.effects is not None:
        update_data["effects_jsonb"] = body.effects
    if body.sell_price is not None:
        update_data["sell_price"] = body.sell_price
    if body.stackable is not None:
        update_data["stackable"] = body.stackable

    updated_item = await repo.update_item(item_id, **update_data)
    assert updated_item is not None

    item_dict = {
        "item_id": updated_item.item_id,
        "item_key": updated_item.item_key,
        "item_type": updated_item.item_type,
        "item_slot": updated_item.item_slot,
        "name": updated_item.name,
        "description": updated_item.description,
        "rarity": updated_item.rarity,
        "chapter_id": updated_item.chapter_id,
        "level_requirement": updated_item.level_requirement,
        "stats": updated_item.stats_jsonb,
        "effects": updated_item.effects_jsonb,
        "sell_price": updated_item.sell_price,
        "stackable": updated_item.stackable,
        "schema_version": updated_item.schema_version,
        "created_at": updated_item.created_at,
        "updated_at": updated_item.updated_at,
    }

    record_item_update()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_ITEM_UPDATE,
        resource_type=RESOURCE_ITEM_DEFINITION,
        resource_id=item_id,
        request_payload_jsonb=body.model_dump(mode="json"),
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=ItemResponse(**item_dict),
        trace_id=x_trace_id,
    )


@ops_router.delete(
    "/world/items/{item_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Item not found"},
    },
    tags=["ops"],
)
async def delete_item(
    item_id: uuid.UUID,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[dict[str, object]]:
    request_id = _make_request_id("req_ops_item_delete")

    repo = ItemDefinitionRepository(db)
    item = await repo.get_item_by_id(item_id)

    if item is None:
        raise_world_error(
            WorldErrorCodes.ITEM_NOT_FOUND,
            "物品不存在",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="path",
                    field="item_id",
                    issue="not_found",
                    rejected_value=str(item_id),
                )
            ],
        )

    success = await repo.delete_item(item_id)
    assert success

    record_item_delete()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_ITEM_DELETE,
        resource_type=RESOURCE_ITEM_DEFINITION,
        resource_id=item_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data={"success": True, "item_id": str(item_id)},
        trace_id=x_trace_id,
    )


# ==================== Monster API ====================


@router.get(
    "/world/monsters",
    summary="获取怪物定义列表",
    response_model=EnvelopeResponse,
)
async def list_monsters(
    monster_type: str | None = Query(None, description="按怪物类型筛选"),
    chapter_id: str | None = Query(None, description="按章节ID筛选"),
    region_key: str | None = Query(None, description="按区域Key筛选"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserPayload = RequireWorldReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse:
    """获取怪物定义列表（公开接口，monsters:read Scope）。"""
    repo = MonsterDefinitionRepository(db)
    monsters, total = await repo.list_monsters(
        monster_type=monster_type,
        chapter_id=chapter_id,
        region_key=region_key,
        limit=limit,
        offset=offset,
    )
    monster_responses = [MonsterResponse.model_validate(m) for m in monsters]
    return EnvelopeResponse(
        request_id="",
        data=MonsterListResponse(monsters=monster_responses, total=total).model_dump(),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset).model_dump(),
    )


@router.get(
    "/world/monsters/{monster_id}",
    summary="获取怪物定义详情",
    response_model=EnvelopeResponse,
)
async def get_monster(
    monster_id: uuid.UUID,
    current_user: UserPayload = RequireWorldReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse:
    """获取单个怪物定义详情（公开接口，monsters:read Scope）。"""
    repo = MonsterDefinitionRepository(db)
    monster = await repo.get_monster_by_id(monster_id)
    if monster is None:
        raise_world_error(
            WorldErrorCodes.MONSTER_NOT_FOUND,
            f"怪物不存在: {monster_id}",
            request_id=_make_request_id("req_world_monster"),
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return EnvelopeResponse(
        request_id="",
        data=MonsterResponse.model_validate(monster).model_dump(),
    )


@ops_router.post(
    "/world/monsters",
    summary="创建怪物定义",
    response_model=EnvelopeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_monster(
    body: CreateMonsterRequest,
    x_trace_id: str | None = Header(None, alias="X-Trace-Id"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    x_request_id: str | None = Header(None, alias="X-Request-Id"),
    current_user: UserPayload = RequireOpsRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse:
    """创建怪物定义（运营接口，ops:monsters:write Scope）。"""
    request_id = x_request_id or _make_request_id("req_ops_monster")

    repo = MonsterDefinitionRepository(db)

    existing = await repo.get_monster_by_key(body.monster_key)
    if existing is not None:
        raise_world_error(
            WorldErrorCodes.MONSTER_KEY_EXISTS,
            f"怪物Key已存在: {body.monster_key}",
            request_id=request_id,
            status_code=status.HTTP_409_CONFLICT,
            details=[
                ErrorDetail(
                    location="body",
                    field="monster_key",
                    issue="already_exists",
                    rejected_value=body.monster_key,
                )
            ],
        )

    monster = await repo.create_monster(
        monster_key=body.monster_key,
        name=body.name,
        monster_type=body.monster_type.value,
        chapter_id=body.chapter_id,
        region_key=body.region_key,
        level=body.level,
        hp=body.hp,
        attack=body.attack,
        defense=body.defense,
        speed=body.speed,
        description=body.description,
        behavior_pattern=body.behavior_pattern,
        loot_table=body.loot_table,
        skills=body.skills,
        min_reputation=body.min_reputation,
    )

    record_monster_create()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_MONSTER_CREATE,
        resource_type=RESOURCE_MONSTER_DEFINITION,
        resource_id=monster.monster_id,
        request_payload_jsonb=body.model_dump(mode="json"),
        result_status=201,
    )

    response_data = CreateMonsterResponse(
        monster_id=monster.monster_id,
        monster_key=monster.monster_key,
        monster_type=MonsterType(monster.monster_type),
        name=monster.name,
        level=monster.level,
        request_id=request_id,
        trace_id=x_trace_id,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data.model_dump(),
        trace_id=x_trace_id,
    )


# ==================== Boss API ====================


@router.get(
    "/world/bosses",
    summary="获取区域Boss列表",
    response_model=EnvelopeResponse,
)
async def list_bosses(
    region_key: str | None = Query(None, description="按区域Key筛选"),
    chapter_id: str | None = Query(None, description="按章节ID筛选"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserPayload = RequireWorldReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse:
    """获取区域Boss列表（公开接口，monsters:read Scope）。"""
    repo = MonsterDefinitionRepository(db)
    bosses, total = await repo.list_bosses(
        region_key=region_key,
        chapter_id=chapter_id,
        limit=limit,
        offset=offset,
    )
    boss_responses = [MonsterResponse.model_validate(b) for b in bosses]
    return EnvelopeResponse(
        request_id=_make_request_id("req_world_bosses"),
        data=BossListResponse(bosses=boss_responses, total=total).model_dump(),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset).model_dump(),
    )


@router.get(
    "/world/bosses/{monster_key}",
    summary="获取Boss详情",
    response_model=EnvelopeResponse,
)
async def get_boss(
    monster_key: str,
    current_user: UserPayload = RequireWorldReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse:
    """获取单个Boss详情（公开接口，monsters:read Scope）。"""
    repo = MonsterDefinitionRepository(db)
    boss = await repo.get_boss_by_key(monster_key)
    if boss is None:
        raise_world_error(
            WorldErrorCodes.MONSTER_NOT_FOUND,
            f"Boss不存在: {monster_key}",
            request_id=_make_request_id("req_world_boss"),
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return EnvelopeResponse(
        request_id=_make_request_id("req_world_boss"),
        data=MonsterResponse.model_validate(boss).model_dump(),
    )


@ops_router.post(
    "/world/monsters/bosses",
    summary="创建Boss定义",
    response_model=EnvelopeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_boss(
    body: CreateBossRequest,
    x_trace_id: str | None = Header(None, alias="X-Trace-Id"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    x_request_id: str | None = Header(None, alias="X-Request-Id"),
    current_user: UserPayload = RequireOpsRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse:
    """创建Boss定义（运营接口，ops:monsters:write Scope）。"""
    request_id = x_request_id or _make_request_id("req_ops_boss")

    repo = MonsterDefinitionRepository(db)

    existing = await repo.get_monster_by_key(body.monster_key)
    if existing is not None:
        raise_world_error(
            WorldErrorCodes.MONSTER_KEY_EXISTS,
            f"Boss Key已存在: {body.monster_key}",
            request_id=request_id,
            status_code=status.HTTP_409_CONFLICT,
            details=[
                ErrorDetail(
                    location="body",
                    field="monster_key",
                    issue="already_exists",
                    rejected_value=body.monster_key,
                )
            ],
        )

    boss = await repo.create_boss(
        monster_key=body.monster_key,
        name=body.name,
        chapter_id=body.chapter_id,
        region_key=body.region_key,
        level=body.level,
        hp=body.hp,
        attack=body.attack,
        defense=body.defense,
        speed=body.speed,
        description=body.description,
        behavior_pattern=body.behavior_pattern,
        loot_table=body.loot_table,
        skills=body.skills,
        min_reputation=body.min_reputation,
        boss_rank=body.boss_rank.value,
        phase_count=body.phase_count,
        special_skills=body.special_skills,
        enrage_threshold=body.enrage_threshold,
        reward=body.reward,
    )

    record_monster_create()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_MONSTER_CREATE,
        resource_type=RESOURCE_MONSTER_DEFINITION,
        resource_id=boss.monster_id,
        request_payload_jsonb=body.model_dump(mode="json"),
        result_status=201,
    )

    response_data = CreateMonsterResponse(
        monster_id=boss.monster_id,
        monster_key=boss.monster_key,
        monster_type=MonsterType(boss.monster_type),
        name=boss.name,
        level=boss.level,
        request_id=request_id,
        trace_id=x_trace_id,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=response_data.model_dump(),
        trace_id=x_trace_id,
    )
