import uuid

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import (
    RequireAchievementsReadScope,
    RequireAchievementsUnlockScope,
    RequireContributionReadScope,
    RequireFriendsReadScope,
    RequireFriendsWriteScope,
    RequireMessagesReadScope,
    RequireMessagesWriteScope,
    RequireOpsAchievementsWriteScope,
    RequireOpsRole,
    RequirePlayerRole,
    RequireQuestsReadScope,
    RequireQuestsWriteScope,
    UserPayload,
)
from app.core.errors import PlayerErrorCodes, raise_player_error
from app.core.metrics import (
    record_achievement_reward_claimed,
    record_achievement_unlocked,
    record_contribution_add,
    record_experience_gained,
    record_friend_request_accepted,
    record_friend_request_sent,
    record_level_up,
    record_inventory_add,
    record_inventory_remove,
    record_inventory_use,
    record_player_create,
    record_player_region_unlock,
    record_player_update,
    record_private_message_sent,
    record_private_message_read,
    record_quest_accept,
    record_quest_complete,
    record_quest_fail,
    record_quest_progress_update,
    record_reputation_add,
    record_reputation_remove,
    record_reputation_unlock,
)
from app.repositories.audit_repo import (
    ACTION_ACHIEVEMENT_CREATE,
    ACTION_ACHIEVEMENT_REWARD_CLAIM,
    ACTION_ACHIEVEMENT_UNLOCK,
    ACTION_CONTRIBUTION_ADD,
    ACTION_EXPERIENCE_ADD,
    ACTION_FRIEND_DELETE,
    ACTION_FRIEND_REQUEST_ACCEPT,
    ACTION_FRIEND_REQUEST_REJECT,
    ACTION_FRIEND_REQUEST_SEND,
    ACTION_LEVEL_UP,
    ACTION_INVENTORY_ADD,
    ACTION_INVENTORY_REMOVE,
    ACTION_INVENTORY_USE,
    ACTION_PLAYER_CREATE,
    ACTION_PLAYER_UPDATE,
    ACTION_QUEST_ACCEPT,
    ACTION_QUEST_COMPLETE,
    ACTION_QUEST_CREATE,
    ACTION_QUEST_FAIL,
    ACTION_QUEST_PROGRESS_UPDATE,
    ACTION_QUEST_STATUS_UPDATE,
    ACTION_REGION_UNLOCK,
    ACTION_REPUTATION_ADJUST,
    ACTION_REPUTATION_UNLOCK,
    ACTION_PRIVATE_MESSAGE_SEND,
    ACTION_PRIVATE_MESSAGE_READ,
    RESOURCE_ACHIEVEMENT,
    RESOURCE_CONTRIBUTION,
    RESOURCE_EXPERIENCE,
    RESOURCE_FRIENDSHIP,
    RESOURCE_INVENTORY,
    RESOURCE_PLAYER,
    RESOURCE_PLAYER_ACHIEVEMENT,
    RESOURCE_QUEST,
    RESOURCE_REGION,
    RESOURCE_REPUTATION,
    RESOURCE_PRIVATE_MESSAGE,
    AuditRepository,
)
from app.repositories.achievement_repo import (
    AchievementDefinitionRepository,
    PlayerAchievementRepository,
)
from app.repositories.contribution_repo import ContributionRepository
from app.repositories.friend_repo import FriendRepository
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.private_message_repo import PrivateMessageRepository
from app.repositories.player_quest_repo import PlayerQuestRepository
from app.repositories.player_region_repo import PlayerRegionRepository
from app.repositories.player_repo import PlayerRepository
from app.schemas.player import (
    AcceptQuestRequest,
    AchievementDefinitionListResponse,
    AchievementDefinitionResponse,
    AchievementCategory,
    AchievementRarity,
    AcceptFriendRequestRequest,
    AddContributionRequest,
    AddExperienceRequest,
    AddItemRequest,
    AdjustReputationRequest,
    CompleteQuestRequest,
    ContributionListResponse,
    ContributionResponse,
    CreateAchievementRequest,
    CreatePlayerQuestRequest,
    CreatePlayerRequest,
    EnvelopeResponse,
    ErrorDetail,
    FailQuestRequest,
    FriendListResponse,
    FriendListItemResponse,
    FriendRequestListResponse,
    FriendRequestItemResponse,
    FriendStatusResponse,
    FriendshipResponse,
    SendMessageRequest,
    PrivateMessageResponse,
    ConversationResponse,
    ConversationListResponse,
    MessageListResponse,
    UnreadCountResponse,
    get_level_progress,
    HealthResponse,
    InventoryItemResponse,
    ItemType,
    PaginatedMeta,
    PlayerAchievementListResponse,
    PlayerAchievementResponse,
    PlayerLevelResponse,
    PlayerProfileResponse,
    PlayerQuestResponse,
    PlayerRegionResponse,
    PlayerResponse,
    QuestStatus,
    RegionReputationResponse,
    RejectFriendRequestRequest,
    RemoveItemRequest,
    SendFriendRequestRequest,
    UnlockAchievementRequest,
    UpdatePlayerRequest,
    UpdateQuestProgressRequest,
    UpdateQuestStatusRequest,
    UseItemRequest,
    get_reputation_level,
    REPUTATION_LEVEL_THRESHOLDS,
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
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    repo = PlayerRepository(db)
    player = await repo.get_player_by_id(player_uuid)

    if player is None:
        raise_player_error(
            PlayerErrorCodes.PLAYER_NOT_FOUND,
            "玩家不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=PlayerResponse.model_validate(player),
        trace_id=trace_id,
    )


@router.get(
    "/player/profile",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Player not found"},
    },
    tags=["player"],
)
async def get_player_profile(
    request: Request,
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[PlayerProfileResponse]:
    """获取玩家完整信息聚合（基本信息+贡献度+声望+成就统计）"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_player_profile")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 1. 获取玩家基本信息
    player_repo = PlayerRepository(db)
    player = await player_repo.get_player_by_id(player_uuid)

    if player is None:
        raise_player_error(
            PlayerErrorCodes.PLAYER_NOT_FOUND,
            "玩家不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # 2. 获取声望汇总
    region_repo = PlayerRegionRepository(db)
    regions, _ = await region_repo.get_player_regions(player_uuid, limit=100, offset=0)
    reputation_summary = [
        _build_region_reputation_response(r.region_id, r.reputation)
        for r in regions
    ]

    # 3. 获取成就统计
    player_achievement_repo = PlayerAchievementRepository(db)
    achievements_unlocked, _ = await player_achievement_repo.get_player_achievements(
        player_uuid, limit=1, offset=0
    )

    achievement_repo = AchievementDefinitionRepository(db)
    all_achievements, achievements_total = await achievement_repo.list_definitions(
        is_active=True, limit=1, offset=0
    )

    # 4. 计算等级进度
    exp = player.experience_points or 0
    level, next_level_exp, level_progress = get_level_progress(exp)

    # 5. 构建聚合响应
    profile = PlayerProfileResponse(
        player_id=player.player_id,
        display_name=player.display_name,
        chapter_id=player.chapter_id,
        level=level,
        experience_points=exp,
        next_level_experience=next_level_exp,
        level_progress=round(level_progress, 4),
        contribution_points=player.contribution_points or 0,
        reputation_summary=reputation_summary,
        achievements_unlocked=len(achievements_unlocked) if achievements_unlocked else 0,
        achievements_total=achievements_total,
        created_at=player.created_at,
        updated_at=player.updated_at,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=profile,
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
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if quest_status is not None and quest_status not in [s.value for s in QuestStatus]:
        raise_player_error(
            PlayerErrorCodes.INVALID_QUEST_STATUS,
            f"无效的任务状态: {quest_status}",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
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
    "/player/quests/{quest_id}",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Quest not found"},
    },
    tags=["player"],
)
async def get_player_quest_detail(
    quest_id: str,
    request: Request,
    current_user: UserPayload = RequireQuestsReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[PlayerQuestResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_player_quest_detail")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    repo = PlayerQuestRepository(db)
    player_quest = await repo.get_player_quest(player_uuid, quest_id)

    if player_quest is None:
        raise_player_error(
            PlayerErrorCodes.QUEST_NOT_FOUND,
            "任务不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=PlayerQuestResponse.model_validate(player_quest),
        trace_id=trace_id,
    )


@router.post(
    "/player/quests/{quest_id}/accept",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Quest not found"},
        409: {"description": "Quest already accepted or invalid state"},
    },
    tags=["player"],
)
async def accept_quest(
    quest_id: str,
    body: AcceptQuestRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: UserPayload = RequireQuestsWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[PlayerQuestResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_quest_accept")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    repo = PlayerQuestRepository(db)
    player_quest = await repo.get_player_quest(player_uuid, quest_id)

    if player_quest is None:
        raise_player_error(
            PlayerErrorCodes.QUEST_NOT_FOUND,
            "任务不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if player_quest.status == QuestStatus.ACTIVE.value:
        raise_player_error(
            PlayerErrorCodes.QUEST_ALREADY_ACCEPTED,
            "任务已接取",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    if player_quest.status != QuestStatus.AVAILABLE.value:
        raise_player_error(
            PlayerErrorCodes.QUEST_INVALID_STATE_TRANSITION,
            f"当前任务状态 {player_quest.status} 不允许接取",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    player_quest = await repo.accept_quest(player_uuid, quest_id)
    assert player_quest is not None
    record_quest_accept()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_QUEST_ACCEPT,
        resource_type=RESOURCE_QUEST,
        resource_id=player_quest.player_quest_id,
        request_payload_jsonb={"quest_id": quest_id},
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=PlayerQuestResponse.model_validate(player_quest),
        trace_id=trace_id,
    )


@router.post(
    "/player/quests/{quest_id}/progress",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Quest not found"},
        409: {"description": "Quest not active"},
    },
    tags=["player"],
)
async def update_quest_progress(
    quest_id: str,
    body: UpdateQuestProgressRequest,
    request: Request,
    current_user: UserPayload = RequireQuestsWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[PlayerQuestResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_quest_progress_update")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    repo = PlayerQuestRepository(db)
    player_quest = await repo.get_player_quest(player_uuid, quest_id)

    if player_quest is None:
        raise_player_error(
            PlayerErrorCodes.QUEST_NOT_FOUND,
            "任务不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if player_quest.status != QuestStatus.ACTIVE.value:
        raise_player_error(
            PlayerErrorCodes.QUEST_NOT_ACTIVE,
            "任务未处于活跃状态，无法更新进度",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    player_quest = await repo.update_objectives(
        player_uuid, quest_id, body.objectives
    )
    assert player_quest is not None
    record_quest_progress_update()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_QUEST_PROGRESS_UPDATE,
        resource_type=RESOURCE_QUEST,
        resource_id=player_quest.player_quest_id,
        request_payload_jsonb={"quest_id": quest_id, "objectives": body.objectives},
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=PlayerQuestResponse.model_validate(player_quest),
        trace_id=trace_id,
    )


@router.post(
    "/player/quests/{quest_id}/complete",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Quest not found"},
        409: {"description": "Quest not active or already completed or objectives incomplete"},
    },
    tags=["player"],
)
async def complete_quest(
    quest_id: str,
    body: CompleteQuestRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: UserPayload = RequireQuestsWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[PlayerQuestResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_quest_complete")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    repo = PlayerQuestRepository(db)
    player_quest = await repo.get_player_quest(player_uuid, quest_id)

    if player_quest is None:
        raise_player_error(
            PlayerErrorCodes.QUEST_NOT_FOUND,
            "任务不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if player_quest.status == QuestStatus.COMPLETED.value:
        raise_player_error(
            PlayerErrorCodes.QUEST_ALREADY_COMPLETED,
            "任务已完成",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    if player_quest.status != QuestStatus.ACTIVE.value:
        raise_player_error(
            PlayerErrorCodes.QUEST_INVALID_STATE_TRANSITION,
            f"当前任务状态 {player_quest.status} 不允许完成",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    player_quest = await repo.complete_quest(player_uuid, quest_id)
    if player_quest is None:
        raise_player_error(
            PlayerErrorCodes.QUEST_OBJECTIVES_INCOMPLETE,
            "任务目标未全部完成，无法提交",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    player_repo = PlayerRepository(db)
    await player_repo.grant_rewards(player_uuid, player_quest.rewards_jsonb)

    if player_quest.rewards_jsonb and isinstance(player_quest.rewards_jsonb, dict):
        rep_rewards = player_quest.rewards_jsonb.get("reputation", {})
        if isinstance(rep_rewards, dict):
            region_repo = PlayerRegionRepository(db)
            audit_repo = AuditRepository(db)
            for region_id, rep_amount in rep_rewards.items():
                if isinstance(rep_amount, int) and rep_amount != 0:
                    await region_repo.add_reputation(player_uuid, region_id, rep_amount)
                    if rep_amount > 0:
                        record_reputation_add()
                    else:
                        record_reputation_remove()
                    unlocked = await region_repo.check_and_unlock_by_reputation(
                        player_uuid, region_id
                    )
                    if unlocked:
                        record_reputation_unlock()
                        record_player_region_unlock()
                        player_region = await region_repo.get_region_reputation(
                            player_uuid, region_id
                        )
                        if player_region is not None:
                            await audit_repo.create_audit_log(
                                trace_id=trace_id or _make_request_id("trace"),
                                request_id=request_id,
                                operator_id=current_user.user_id,
                                operator_role=current_user.role.value,
                                action=ACTION_REPUTATION_UNLOCK,
                                resource_type=RESOURCE_REGION,
                                resource_id=player_region.player_region_id,
                                reason="reputation_threshold_reached",
                                request_payload_jsonb={
                                    "region_id": region_id,
                                    "reputation": player_region.reputation,
                                },
                                result_status=200,
                            )

    contribution_points = 0
    experience_points = 0
    if player_quest.rewards_jsonb and isinstance(player_quest.rewards_jsonb, dict):
        raw_cp = player_quest.rewards_jsonb.get("contribution_points", 0)
        if isinstance(raw_cp, int) and raw_cp > 0:
            contribution_points = raw_cp
        raw_exp = player_quest.rewards_jsonb.get("experience_points", 0)
        if isinstance(raw_exp, int) and raw_exp > 0:
            experience_points = raw_exp

    if contribution_points > 0:
        contribution_repo = ContributionRepository(db)
        await contribution_repo.add_contribution(
            player_id=player_uuid,
            amount=contribution_points,
            source="quest",
            source_id=quest_id,
            description="任务完成奖励",
        )
        record_contribution_add(
            player_id=str(player_uuid), source="quest", amount=contribution_points
        )

    if experience_points > 0:
        player_repo = PlayerRepository(db)
        player, levels_gained = await player_repo.add_experience(
            player_uuid, experience_points
        )
        record_experience_gained(
            player_id=str(player_uuid),
            source="quest",
            amount=experience_points,
        )
        for level in levels_gained:
            record_level_up(
                player_id=str(player_uuid),
                level=level,
            )
            audit_repo = AuditRepository(db)
            await audit_repo.create_audit_log(
                trace_id=trace_id or _make_request_id("trace"),
                request_id=request_id,
                operator_id=current_user.user_id,
                operator_role=current_user.role.value,
                action=ACTION_LEVEL_UP,
                resource_type=RESOURCE_EXPERIENCE,
                resource_id=player.player_id,
                reason="quest_completion",
                request_payload_jsonb={
                    "quest_id": quest_id,
                    "new_level": level,
                },
                result_status=200,
            )

    record_quest_complete()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_QUEST_COMPLETE,
        resource_type=RESOURCE_QUEST,
        resource_id=player_quest.player_quest_id,
        request_payload_jsonb={"quest_id": quest_id, "rewards": player_quest.rewards_jsonb},
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=PlayerQuestResponse.model_validate(player_quest),
        trace_id=trace_id,
    )


@router.post(
    "/player/quests/{quest_id}/fail",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Quest not found"},
        409: {"description": "Quest not active"},
    },
    tags=["player"],
)
async def fail_quest(
    quest_id: str,
    body: FailQuestRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: UserPayload = RequireQuestsWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[PlayerQuestResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_quest_fail")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    repo = PlayerQuestRepository(db)
    player_quest = await repo.get_player_quest(player_uuid, quest_id)

    if player_quest is None:
        raise_player_error(
            PlayerErrorCodes.QUEST_NOT_FOUND,
            "任务不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if player_quest.status != QuestStatus.ACTIVE.value:
        raise_player_error(
            PlayerErrorCodes.QUEST_INVALID_STATE_TRANSITION,
            f"当前任务状态 {player_quest.status} 不允许标记为失败",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    player_quest = await repo.fail_quest(player_uuid, quest_id)
    assert player_quest is not None
    record_quest_fail()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_QUEST_FAIL,
        resource_type=RESOURCE_QUEST,
        resource_id=player_quest.player_quest_id,
        request_payload_jsonb={"quest_id": quest_id},
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=PlayerQuestResponse.model_validate(player_quest),
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
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
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
        raise_player_error(
            PlayerErrorCodes.PLAYER_NOT_FOUND,
            "玩家不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
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
        raise_player_error(
            PlayerErrorCodes.PLAYER_NOT_FOUND,
            "玩家不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
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

    player_repo = PlayerRepository(db)
    player = await player_repo.get_player_by_id(player_id)
    if player is None:
        raise_player_error(
            PlayerErrorCodes.PLAYER_NOT_FOUND,
            "玩家不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

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


@ops_router.get(
    "/players/{player_id}/quests",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Player not found"},
    },
    tags=["ops"],
)
async def ops_get_player_quests(
    player_id: uuid.UUID,
    request: Request,
    status_filter: QuestStatus | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[list[PlayerQuestResponse]]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_ops_player_quests")

    player_repo = PlayerRepository(db)
    player = await player_repo.get_player_by_id(player_id)
    if player is None:
        raise_player_error(
            PlayerErrorCodes.PLAYER_NOT_FOUND,
            "玩家不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    repo = PlayerQuestRepository(db)
    quests, total = await repo.get_player_quests(
        player_id,
        status=status_filter.value if status_filter else None,
        limit=limit,
        offset=offset,
    )

    quest_responses = [PlayerQuestResponse.model_validate(q) for q in quests]

    return EnvelopeResponse(
        request_id=request_id,
        data=quest_responses,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@ops_router.post(
    "/players/{player_id}/quests",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Player not found"},
        409: {"description": "Quest already exists"},
    },
    tags=["ops"],
)
async def create_player_quest(
    player_id: uuid.UUID,
    body: CreatePlayerQuestRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[PlayerQuestResponse]:
    request_id = _make_request_id("req_ops_player_quest_create")

    player_repo = PlayerRepository(db)
    player = await player_repo.get_player_by_id(player_id)
    if player is None:
        raise_player_error(
            PlayerErrorCodes.PLAYER_NOT_FOUND,
            "玩家不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    repo = PlayerQuestRepository(db)
    existing = await repo.get_player_quest(player_id, body.quest_id)
    if existing is not None:
        raise_player_error(
            PlayerErrorCodes.QUEST_ALREADY_ACCEPTED,
            "该任务已存在于玩家任务列表中",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    player_quest = await repo.create_player_quest(
        player_id=player_id,
        quest_id=body.quest_id,
        status=body.status.value,
        objectives_jsonb=body.objectives_jsonb,
        rewards_jsonb=body.rewards_jsonb,
    )

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_QUEST_CREATE,
        resource_type=RESOURCE_QUEST,
        resource_id=player_quest.player_quest_id,
        request_payload_jsonb={"player_id": str(player_id), **body.model_dump(mode="json")},
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=PlayerQuestResponse.model_validate(player_quest),
        trace_id=x_trace_id,
    )


@ops_router.patch(
    "/players/{player_id}/quests/{quest_id}/status",
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Quest not found"},
        409: {"description": "Invalid state transition"},
    },
    tags=["ops"],
)
async def update_player_quest_status(
    player_id: uuid.UUID,
    quest_id: str,
    body: UpdateQuestStatusRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[PlayerQuestResponse]:
    request_id = _make_request_id("req_ops_quest_status_update")

    repo = PlayerQuestRepository(db)
    player_quest = await repo.get_player_quest(player_id, quest_id)

    if player_quest is None:
        raise_player_error(
            PlayerErrorCodes.QUEST_NOT_FOUND,
            "任务不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    player_quest = await repo.update_status(
        player_id, quest_id, body.status.value
    )

    if player_quest is None:
        raise_player_error(
            PlayerErrorCodes.QUEST_INVALID_STATE_TRANSITION,
            "无效的任务状态转换",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_QUEST_STATUS_UPDATE,
        resource_type=RESOURCE_QUEST,
        resource_id=player_quest.player_quest_id,
        request_payload_jsonb={
            "player_id": str(player_id),
            "quest_id": quest_id,
            "status": body.status.value,
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=PlayerQuestResponse.model_validate(player_quest),
        trace_id=x_trace_id,
    )


# --- Inventory API ---


@router.get(
    "/player/inventory",
    responses={
        401: {"description": "Unauthorized"},
        400: {"description": "Invalid player ID"},
    },
    tags=["player"],
)
async def get_player_inventory(
    request: Request,
    current_user: UserPayload = RequirePlayerRole,
    item_type: str | None = Query(default=None, alias="type"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[InventoryItemResponse]]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_player_inventory")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if item_type is not None and item_type not in [t.value for t in ItemType]:
        raise_player_error(
            PlayerErrorCodes.INVALID_ITEM_TYPE,
            f"无效的物品类型: {item_type}",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    repo = InventoryRepository(db)
    items, total = await repo.get_inventory(player_uuid, limit=limit, offset=offset)

    if item_type is not None:
        items = [i for i in items if i.item_type == item_type]

    item_responses = [InventoryItemResponse.model_validate(i) for i in items]

    return EnvelopeResponse(
        request_id=request_id,
        data=item_responses,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.post(
    "/player/inventory/use",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Item not found"},
        409: {"description": "Insufficient quantity or invalid item type"},
    },
    tags=["player"],
)
async def use_inventory_item(
    body: UseItemRequest,
    request: Request,
    item_key: str = Query(..., alias="item_key"),
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[InventoryItemResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_inventory_use")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    repo = InventoryRepository(db)
    item = await repo.use_item(player_uuid, item_key, body.quantity)

    record_inventory_use()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_INVENTORY_USE,
        resource_type=RESOURCE_INVENTORY,
        resource_id=item.inventory_id,
        request_payload_jsonb={"item_key": item_key, "quantity": body.quantity},
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=InventoryItemResponse.model_validate(item),
        trace_id=trace_id,
    )


@ops_router.post(
    "/players/{player_id}/inventory",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Player not found"},
    },
    tags=["ops"],
)
async def ops_add_inventory_item(
    player_id: uuid.UUID,
    body: AddItemRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[InventoryItemResponse]:
    request_id = _make_request_id("req_ops_inventory_add")

    player_repo = PlayerRepository(db)
    player = await player_repo.get_player_by_id(player_id)
    if player is None:
        raise_player_error(
            PlayerErrorCodes.PLAYER_NOT_FOUND,
            "玩家不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    repo = InventoryRepository(db)
    item = await repo.add_item(
        player_id=player_id,
        item_key=body.item_key,
        item_type=body.item_type.value,
        quantity=body.quantity,
        metadata_jsonb=body.metadata_jsonb,
    )

    record_inventory_add()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_INVENTORY_ADD,
        resource_type=RESOURCE_INVENTORY,
        resource_id=item.inventory_id,
        request_payload_jsonb={"player_id": str(player_id), **body.model_dump(mode="json")},
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=InventoryItemResponse.model_validate(item),
        trace_id=x_trace_id,
    )


@ops_router.delete(
    "/players/{player_id}/inventory/{item_key}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Item not found"},
        409: {"description": "Insufficient quantity"},
    },
    tags=["ops"],
)
async def ops_remove_inventory_item(
    player_id: uuid.UUID,
    item_key: str,
    body: RemoveItemRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[InventoryItemResponse]:
    request_id = _make_request_id("req_ops_inventory_remove")

    repo = InventoryRepository(db)
    item = await repo.remove_item(player_id, item_key, body.quantity)

    record_inventory_remove()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_INVENTORY_REMOVE,
        resource_type=RESOURCE_INVENTORY,
        resource_id=item.inventory_id,
        request_payload_jsonb={
            "player_id": str(player_id),
            "item_key": item_key,
            "quantity": body.quantity,
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=InventoryItemResponse.model_validate(item),
        trace_id=x_trace_id,
    )


# --- Reputation API ---


def _build_region_reputation_response(region_id: str, reputation: int) -> RegionReputationResponse:
    level = get_reputation_level(reputation)
    thresholds = list(REPUTATION_LEVEL_THRESHOLDS.values())
    level_names = list(REPUTATION_LEVEL_THRESHOLDS.keys())
    current_idx = level_names.index(level.value)

    if current_idx < len(thresholds) - 1:
        next_threshold = thresholds[current_idx + 1]
        current_threshold = thresholds[current_idx]
        progress_range = next_threshold - current_threshold
        current_progress = reputation - current_threshold
        progress = min(1.0, max(0.0, current_progress / progress_range)) if progress_range > 0 else 1.0
    else:
        next_threshold = thresholds[-1]
        progress = 1.0

    return RegionReputationResponse(
        region_id=region_id,
        reputation=reputation,
        reputation_level=level,
        next_level_threshold=next_threshold,
        current_level_progress=round(progress, 4),
    )


@router.get(
    "/player/reputation/{region_id}",
    responses={
        401: {"description": "Unauthorized"},
        400: {"description": "Invalid player ID"},
    },
    tags=["player"],
)
async def get_region_reputation(
    region_id: str,
    request: Request,
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[RegionReputationResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_reputation_get")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    repo = PlayerRegionRepository(db)
    player_region = await repo.get_region_reputation(player_uuid, region_id)
    reputation = player_region.reputation if player_region else 0

    return EnvelopeResponse(
        request_id=request_id,
        data=_build_region_reputation_response(region_id, reputation),
        trace_id=trace_id,
    )


@router.get(
    "/player/reputation",
    responses={
        401: {"description": "Unauthorized"},
        400: {"description": "Invalid player ID"},
    },
    tags=["player"],
)
async def get_all_reputation(
    request: Request,
    current_user: UserPayload = RequirePlayerRole,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[RegionReputationResponse]]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_reputation_list")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    repo = PlayerRegionRepository(db)
    regions, total = await repo.get_player_regions(player_uuid, limit=limit, offset=offset)

    reputation_responses = [
        _build_region_reputation_response(r.region_id, r.reputation)
        for r in regions
    ]

    return EnvelopeResponse(
        request_id=request_id,
        data=reputation_responses,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@ops_router.post(
    "/players/{player_id}/reputation/{region_id}/adjust",
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Player not found"},
    },
    tags=["ops"],
)
async def adjust_region_reputation(
    player_id: uuid.UUID,
    region_id: str,
    body: AdjustReputationRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[RegionReputationResponse]:
    request_id = _make_request_id("req_ops_reputation_adjust")

    player_repo = PlayerRepository(db)
    player = await player_repo.get_player_by_id(player_id)
    if player is None:
        raise_player_error(
            PlayerErrorCodes.PLAYER_NOT_FOUND,
            "玩家不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    repo = PlayerRegionRepository(db)
    player_region = await repo.add_reputation(player_id, region_id, body.amount)

    if body.amount > 0:
        record_reputation_add()
    elif body.amount < 0:
        record_reputation_remove()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_REPUTATION_ADJUST,
        resource_type=RESOURCE_REPUTATION,
        resource_id=player_region.player_region_id,
        reason=body.reason,
        request_payload_jsonb={
            "player_id": str(player_id),
            "region_id": region_id,
            "amount": body.amount,
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=_build_region_reputation_response(region_id, player_region.reputation),
        trace_id=x_trace_id,
    )


# --- Level & Experience API ---


@router.get(
    "/player/level",
    responses={
        401: {"description": "Unauthorized"},
        400: {"description": "Invalid player ID"},
    },
    tags=["player"],
)
async def get_player_level(
    request: Request,
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[PlayerLevelResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_player_level")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    player_repo = PlayerRepository(db)
    player = await player_repo.get_player_by_id(player_uuid)

    if player is None:
        raise_player_error(
            PlayerErrorCodes.PLAYER_NOT_FOUND,
            "玩家不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    exp = player.experience_points or 0
    level, next_level_exp, level_progress = get_level_progress(exp)

    return EnvelopeResponse(
        request_id=request_id,
        data=PlayerLevelResponse(
            player_id=player.player_id,
            level=level,
            experience_points=exp,
            next_level_experience=next_level_exp,
            level_progress=round(level_progress, 4),
            updated_at=player.updated_at,
        ),
        trace_id=trace_id,
    )


@ops_router.post(
    "/players/{player_id}/experience",
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Player not found"},
    },
    tags=["ops"],
)
async def add_player_experience(
    player_id: uuid.UUID,
    body: AddExperienceRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[PlayerLevelResponse]:
    request_id = _make_request_id("req_ops_experience_add")

    player_repo = PlayerRepository(db)
    player = await player_repo.get_player_by_id(player_id)
    if player is None:
        raise_player_error(
            PlayerErrorCodes.PLAYER_NOT_FOUND,
            "玩家不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if body.amount <= 0:
        raise_player_error(
            PlayerErrorCodes.INVALID_EXPERIENCE_AMOUNT,
            "经验值必须为正整数",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=[
                ErrorDetail(
                    location="body",
                    field="amount",
                    issue="invalid_amount",
                    rejected_value=str(body.amount),
                )
            ],
        )

    player, levels_gained = await player_repo.add_experience(player_id, body.amount)

    exp = player.experience_points or 0
    level, next_level_exp, level_progress = get_level_progress(exp)

    record_experience_gained(
        player_id=str(player_id),
        source=body.source.value,
        amount=body.amount,
    )
    for level_gained in levels_gained:
        record_level_up(
            player_id=str(player_id),
            level=level_gained,
        )

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_EXPERIENCE_ADD,
        resource_type=RESOURCE_EXPERIENCE,
        resource_id=player_id,
        reason=body.reason,
        request_payload_jsonb={
            "player_id": str(player_id),
            "amount": body.amount,
            "source": body.source.value,
            "source_id": body.source_id,
            "levels_gained": levels_gained,
        },
        result_status=200,
    )

    for level_gained in levels_gained:
        await audit_repo.create_audit_log(
            trace_id=x_trace_id or _make_request_id("trace"),
            request_id=request_id,
            operator_id=current_user.user_id,
            operator_role=current_user.role.value,
            action=ACTION_LEVEL_UP,
            resource_type=RESOURCE_EXPERIENCE,
            resource_id=player_id,
            reason=body.reason or "ops_adjustment",
            request_payload_jsonb={
                "player_id": str(player_id),
                "new_level": level_gained,
                "source": body.source.value,
            },
            result_status=200,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=PlayerLevelResponse(
            player_id=player.player_id,
            level=level,
            experience_points=exp,
            next_level_experience=next_level_exp,
            level_progress=round(level_progress, 4),
            updated_at=player.updated_at,
        ),
        trace_id=x_trace_id,
    )


# --- Contribution API ---


@router.get(
    "/player/contribution",
    responses={
        401: {"description": "Unauthorized"},
        400: {"description": "Invalid player ID"},
    },
    tags=["player"],
)
async def get_player_contribution(
    request: Request,
    current_user: UserPayload = RequireContributionReadScope,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[ContributionListResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_player_contribution")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    contribution_repo = ContributionRepository(db)
    contribution_points = await contribution_repo.get_player_contribution(player_uuid)
    contributions, total = await contribution_repo.list_contributions(
        player_uuid, limit=limit, offset=offset
    )

    contribution_responses = [
        ContributionResponse.model_validate(c) for c in contributions
    ]

    return EnvelopeResponse(
        request_id=request_id,
        data=ContributionListResponse(
            contribution_points=contribution_points,
            contributions=contribution_responses,
            total=total,
        ),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@ops_router.post(
    "/players/{player_id}/contribution",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Player not found"},
    },
    tags=["ops"],
)
async def add_player_contribution(
    player_id: uuid.UUID,
    body: AddContributionRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsRole,
) -> EnvelopeResponse[ContributionResponse]:
    request_id = _make_request_id("req_ops_contribution_add")

    contribution_repo = ContributionRepository(db)

    try:
        contribution = await contribution_repo.add_contribution(
            player_id=player_id,
            amount=body.amount,
            source=body.source.value,
            source_id=body.source_id,
            description=body.description,
        )
    except ValueError as exc:
        message = str(exc)
        if "玩家不存在" in message:
            raise_player_error(
                PlayerErrorCodes.CONTRIBUTION_PLAYER_NOT_FOUND,
                "玩家不存在",
                request_id,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        raise_player_error(
            PlayerErrorCodes.INVALID_CONTRIBUTION_AMOUNT,
            message,
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    record_contribution_add(
        player_id=str(player_id), source=body.source.value, amount=body.amount
    )

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_CONTRIBUTION_ADD,
        resource_type=RESOURCE_CONTRIBUTION,
        resource_id=contribution.contribution_id,
        request_payload_jsonb={
            "player_id": str(player_id),
            **body.model_dump(mode="json"),
        },
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=ContributionResponse.model_validate(contribution),
        trace_id=x_trace_id,
    )


@router.get("/player/achievements", tags=["achievements"])
async def list_achievement_definitions(
    request: Request,
    category: AchievementCategory | None = Query(default=None),
    rarity: AchievementRarity | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireAchievementsReadScope,
) -> EnvelopeResponse[AchievementDefinitionListResponse]:
    request_id = _make_request_id("req_achievement_list")
    trace_id = _get_trace_id(request)

    achievement_repo = AchievementDefinitionRepository(db)
    achievements, total = await achievement_repo.list_definitions(
        category=category.value if category else None,
        rarity=rarity.value if rarity else None,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=AchievementDefinitionListResponse(
            achievements=[
                AchievementDefinitionResponse.model_validate(a) for a in achievements
            ],
            total=total,
        ),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get("/player/achievements/{achievement_key}", tags=["achievements"])
async def get_achievement_definition(
    achievement_key: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireAchievementsReadScope,
) -> EnvelopeResponse[AchievementDefinitionResponse]:
    request_id = _make_request_id("req_achievement_get")
    trace_id = _get_trace_id(request)

    achievement_repo = AchievementDefinitionRepository(db)
    achievement = await achievement_repo.get_definition(achievement_key)
    if achievement is None:
        raise_player_error(
            PlayerErrorCodes.ACHIEVEMENT_NOT_FOUND,
            "成就不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
            details=[
                ErrorDetail(
                    location="path",
                    field="achievement_key",
                    issue="not_found",
                    rejected_value=achievement_key,
                )
            ],
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=AchievementDefinitionResponse.model_validate(achievement),
        trace_id=trace_id,
    )


@router.get("/player/me/achievements", tags=["achievements"])
async def list_my_achievements(
    request: Request,
    x_player_id: uuid.UUID = Header(..., alias="X-Player-Id"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireAchievementsReadScope,
) -> EnvelopeResponse[PlayerAchievementListResponse]:
    request_id = _make_request_id("req_player_achievement_list")
    trace_id = _get_trace_id(request)

    player_achievement_repo = PlayerAchievementRepository(db)
    achievements, total = await player_achievement_repo.get_player_achievements(
        x_player_id, limit=limit, offset=offset
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=PlayerAchievementListResponse(
            achievements=[
                PlayerAchievementResponse.model_validate(a) for a in achievements
            ],
            total=total,
        ),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.post(
    "/player/me/achievements/{achievement_key}/claim",
    tags=["achievements"],
)
async def claim_achievement_reward(
    achievement_key: str,
    request: Request,
    x_player_id: uuid.UUID = Header(..., alias="X-Player-Id"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireAchievementsReadScope,
) -> EnvelopeResponse[PlayerAchievementResponse]:
    request_id = _make_request_id("req_achievement_claim")

    player_achievement_repo = PlayerAchievementRepository(db)

    try:
        achievement = await player_achievement_repo.claim_reward(
            x_player_id, achievement_key
        )
    except ValueError as exc:
        message = str(exc)
        if "玩家未解锁该成就" in message:
            raise_player_error(
                PlayerErrorCodes.ACHIEVEMENT_NOT_FOUND,
                "玩家未解锁该成就",
                request_id,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if "成就奖励已领取" in message:
            raise_player_error(
                PlayerErrorCodes.ACHIEVEMENT_REWARD_ALREADY_CLAIMED,
                "成就奖励已领取",
                request_id,
                status_code=status.HTTP_409_CONFLICT,
            )
        raise

    definition_repo = AchievementDefinitionRepository(db)
    definition = await definition_repo.get_definition(achievement_key)
    if definition is not None:
        record_achievement_reward_claimed(
            player_id=str(x_player_id),
            achievement_key=achievement_key,
        )

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_ACHIEVEMENT_REWARD_CLAIM,
        resource_type=RESOURCE_PLAYER_ACHIEVEMENT,
        resource_id=achievement.player_achievement_id,
        request_payload_jsonb={
            "player_id": str(x_player_id),
            "achievement_key": achievement_key,
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=PlayerAchievementResponse.model_validate(achievement),
        trace_id=x_trace_id,
    )


@ops_router.post(
    "/achievements",
    tags=["achievements"],
    status_code=status.HTTP_201_CREATED,
)
async def create_achievement_definition(
    body: CreateAchievementRequest,
    request: Request,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireOpsAchievementsWriteScope,
) -> EnvelopeResponse[AchievementDefinitionResponse]:
    request_id = _make_request_id("req_ops_achievement_create")

    achievement_repo = AchievementDefinitionRepository(db)

    try:
        achievement = await achievement_repo.create_definition(
            achievement_key=body.achievement_key,
            name=body.name,
            description=body.description,
            rarity=body.rarity.value,
            category=body.category.value,
            points=body.points,
            icon=body.icon,
            reward_jsonb=body.reward_jsonb,
            condition_jsonb=body.condition_jsonb,
        )
    except ValueError as exc:
        message = str(exc)
        if "成就键已存在" in message:
            raise_player_error(
                PlayerErrorCodes.ACHIEVEMENT_KEY_EXISTS,
                "成就键已存在",
                request_id,
                status_code=status.HTTP_409_CONFLICT,
                details=[
                    ErrorDetail(
                        location="body",
                        field="achievement_key",
                        issue="already_exists",
                        rejected_value=body.achievement_key,
                    )
                ],
            )
        raise

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_ACHIEVEMENT_CREATE,
        resource_type=RESOURCE_ACHIEVEMENT,
        resource_id=None,
        request_payload_jsonb={
            "achievement_key": achievement.achievement_key,
            **body.model_dump(mode="json"),
        },
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=AchievementDefinitionResponse.model_validate(achievement),
        trace_id=x_trace_id,
    )


@ops_router.post(
    "/players/{player_id}/achievements/{achievement_key}/unlock",
    tags=["achievements"],
    status_code=status.HTTP_201_CREATED,
)
async def unlock_player_achievement(
    player_id: uuid.UUID,
    achievement_key: str,
    body: UnlockAchievementRequest,
    request: Request,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireAchievementsUnlockScope,
) -> EnvelopeResponse[PlayerAchievementResponse]:
    request_id = _make_request_id("req_ops_achievement_unlock")

    player_achievement_repo = PlayerAchievementRepository(db)

    try:
        achievement = await player_achievement_repo.unlock_achievement(
            player_id,
            achievement_key,
            source=body.source.value,
            source_id=body.source_id,
        )
    except ValueError as exc:
        message = str(exc)
        if "玩家不存在" in message:
            raise_player_error(
                PlayerErrorCodes.PLAYER_NOT_FOUND,
                "玩家不存在",
                request_id,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if "成就不存在" in message:
            raise_player_error(
                PlayerErrorCodes.ACHIEVEMENT_NOT_FOUND,
                "成就不存在",
                request_id,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if "成就未激活" in message:
            raise_player_error(
                PlayerErrorCodes.ACHIEVEMENT_NOT_ACTIVE,
                "成就未激活，无法解锁",
                request_id,
                status_code=status.HTTP_409_CONFLICT,
            )
        raise

    definition_repo = AchievementDefinitionRepository(db)
    definition = await definition_repo.get_definition(achievement_key)
    if definition is not None:
        record_achievement_unlocked(
            player_id=str(player_id),
            category=definition.category,
        )

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_ACHIEVEMENT_UNLOCK,
        resource_type=RESOURCE_PLAYER_ACHIEVEMENT,
        resource_id=achievement.player_achievement_id,
        request_payload_jsonb={
            "player_id": str(player_id),
            "achievement_key": achievement_key,
            **body.model_dump(mode="json"),
        },
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=PlayerAchievementResponse.model_validate(achievement),
        trace_id=x_trace_id,
    )


# ============================================================
# 好友系统 API
# ============================================================


@router.post(
    "/player/friends/request",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "不能添加自己为好友"},
        403: {"description": "已被对方拉黑"},
        409: {"description": "好友请求已发送或已是好友"},
    },
    tags=["friends"],
)
async def send_friend_request(
    request: Request,
    body: SendFriendRequestRequest,
    current_user: UserPayload = RequireFriendsWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[FriendshipResponse]:
    """发送好友请求"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_friend_req")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if player_uuid == body.friend_id:
        raise_player_error(
            PlayerErrorCodes.CANNOT_FRIEND_SELF,
            "不能添加自己为好友",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    friend_repo = FriendRepository(db)
    player_repo = PlayerRepository(db)

    friend_player = await player_repo.get_player_by_id(body.friend_id)
    if friend_player is None:
        raise_player_error(
            PlayerErrorCodes.PLAYER_NOT_FOUND,
            "目标玩家不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if await friend_repo.is_blocked(player_uuid, body.friend_id):
        raise_player_error(
            PlayerErrorCodes.FRIEND_BLOCKED,
            "已被对方拉黑",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    existing = await friend_repo.get_friendship(player_uuid, body.friend_id)
    if existing is not None:
        if existing.status == "accepted":
            raise_player_error(
                PlayerErrorCodes.ALREADY_FRIENDS,
                "已经是好友",
                request_id,
                status_code=status.HTTP_409_CONFLICT,
            )
        if existing.status == "pending":
            # 如果当前玩家是已有请求的发起者，说明已发过请求
            if existing.player_id == player_uuid:
                raise_player_error(
                    PlayerErrorCodes.FRIEND_REQUEST_ALREADY_SENT,
                    "好友请求已发送",
                    request_id,
                    status_code=status.HTTP_409_CONFLICT,
                )
            # 如果当前玩家是已有请求的接收者，继续走 repo 的自动接受逻辑
        if existing.status == "blocked":
            raise_player_error(
                PlayerErrorCodes.FRIEND_BLOCKED,
                "好友关系已被拉黑",
                request_id,
                status_code=status.HTTP_403_FORBIDDEN,
            )

    friendship = await friend_repo.send_friend_request(
        player_uuid, body.friend_id
    )

    if friendship.status == "accepted":
        record_friend_request_accepted(player_id=str(player_uuid))
    else:
        record_friend_request_sent(player_id=str(player_uuid))

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_FRIEND_REQUEST_SEND,
        resource_type=RESOURCE_FRIENDSHIP,
        resource_id=friendship.friendship_id,
        request_payload_jsonb={
            "friend_id": str(body.friend_id),
        },
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=FriendshipResponse.model_validate(friendship),
        trace_id=trace_id,
    )


@router.post(
    "/player/friends/accept",
    responses={
        404: {"description": "好友请求不存在"},
        409: {"description": "好友请求非待处理状态"},
    },
    tags=["friends"],
)
async def accept_friend_request(
    request: Request,
    body: AcceptFriendRequestRequest,
    current_user: UserPayload = RequireFriendsWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[FriendshipResponse]:
    """接受好友请求"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_friend_accept")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    friend_repo = FriendRepository(db)
    friendship = await friend_repo.accept_friend_request(
        body.player_id, player_uuid
    )

    if friendship is None:
        raise_player_error(
            PlayerErrorCodes.FRIEND_REQUEST_NOT_FOUND,
            "好友请求不存在或非待处理状态",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    record_friend_request_accepted(player_id=str(player_uuid))

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_FRIEND_REQUEST_ACCEPT,
        resource_type=RESOURCE_FRIENDSHIP,
        resource_id=friendship.friendship_id,
        request_payload_jsonb={
            "player_id": str(body.player_id),
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=FriendshipResponse.model_validate(friendship),
        trace_id=trace_id,
    )


@router.post(
    "/player/friends/reject",
    responses={
        404: {"description": "好友请求不存在"},
        409: {"description": "好友请求非待处理状态"},
    },
    tags=["friends"],
)
async def reject_friend_request(
    request: Request,
    body: RejectFriendRequestRequest,
    current_user: UserPayload = RequireFriendsWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[FriendshipResponse]:
    """拒绝好友请求"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_friend_reject")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    friend_repo = FriendRepository(db)
    friendship = await friend_repo.reject_friend_request(
        body.player_id, player_uuid
    )

    if friendship is None:
        raise_player_error(
            PlayerErrorCodes.FRIEND_REQUEST_NOT_FOUND,
            "好友请求不存在或非待处理状态",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_FRIEND_REQUEST_REJECT,
        resource_type=RESOURCE_FRIENDSHIP,
        resource_id=friendship.friendship_id,
        request_payload_jsonb={
            "player_id": str(body.player_id),
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=FriendshipResponse.model_validate(friendship),
        trace_id=trace_id,
    )


@router.delete(
    "/player/friends/{friend_id}",
    responses={
        404: {"description": "好友关系不存在"},
    },
    tags=["friends"],
)
async def delete_friend(
    friend_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireFriendsWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[dict[str, bool]]:
    """删除好友"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_friend_del")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    friend_repo = FriendRepository(db)
    deleted = await friend_repo.delete_friend(player_uuid, friend_id)

    if not deleted:
        raise_player_error(
            PlayerErrorCodes.FRIEND_NOT_FOUND,
            "好友关系不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_FRIEND_DELETE,
        resource_type=RESOURCE_FRIENDSHIP,
        resource_id=friend_id,
        request_payload_jsonb={
            "friend_id": str(friend_id),
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data={"deleted": True},
        trace_id=trace_id,
    )


@router.get(
    "/player/friends",
    tags=["friends"],
)
async def get_friends(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireFriendsReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[FriendListResponse]:
    """获取好友列表"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_friend_list")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    friend_repo = FriendRepository(db)
    player_repo = PlayerRepository(db)
    friendships, total = await friend_repo.get_friends(
        player_uuid, limit=limit, offset=offset
    )

    friends_list: list[FriendListItemResponse] = []
    for fs in friendships:
        if fs.player_id == player_uuid:
            friend_uuid = fs.friend_id
        else:
            friend_uuid = fs.player_id

        friend_player = await player_repo.get_player_by_id(friend_uuid)
        friend_name = friend_player.display_name if friend_player else "Unknown"
        friend_level = friend_player.level if friend_player else 1

        friends_list.append(
            FriendListItemResponse(
                friendship_id=fs.friendship_id,
                friend_id=friend_uuid,
                friend_display_name=friend_name,
                friend_level=friend_level,
                status=fs.status,
                created_at=fs.created_at,
                updated_at=fs.updated_at,
            )
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=FriendListResponse(friends=friends_list, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/player/friends/requests",
    tags=["friends"],
)
async def get_pending_friend_requests(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireFriendsReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[FriendRequestListResponse]:
    """获取待处理的好友请求"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_friend_pending")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    friend_repo = FriendRepository(db)
    player_repo = PlayerRepository(db)
    friendships, total = await friend_repo.get_pending_requests(
        player_uuid, limit=limit, offset=offset
    )

    requests_list: list[FriendRequestItemResponse] = []
    for fs in friendships:
        requester_player = await player_repo.get_player_by_id(fs.player_id)
        requester_name = (
            requester_player.display_name
            if requester_player
            else "Unknown"
        )
        requester_level = requester_player.level if requester_player else 1

        requests_list.append(
            FriendRequestItemResponse(
                friendship_id=fs.friendship_id,
                player_id=fs.player_id,
                player_display_name=requester_name,
                player_level=requester_level,
                status=fs.status,
                created_at=fs.created_at,
                updated_at=fs.updated_at,
            )
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=FriendRequestListResponse(requests=requests_list, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/player/friends/{friend_id}/status",
    tags=["friends"],
)
async def get_friend_status(
    friend_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireFriendsReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[FriendStatusResponse]:
    """查询好友关系状态"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_friend_status")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    friend_repo = FriendRepository(db)
    friendship = await friend_repo.get_friendship(player_uuid, friend_id)

    if friendship is None:
        return EnvelopeResponse(
            request_id=request_id,
            data=FriendStatusResponse(status="none"),
            trace_id=trace_id,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=FriendStatusResponse(
            friendship_id=friendship.friendship_id,
            player_id=friendship.player_id,
            friend_id=friendship.friend_id,
            status=friendship.status,
        ),
        trace_id=trace_id,
    )


# ===== 私聊消息 API =====


@router.post(
    "/player/messages",
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not friends"},
        400: {"description": "Message empty or too long"},
    },
    tags=["messages"],
)
async def send_private_message(
    body: SendMessageRequest,
    request: Request,
    current_user: UserPayload = RequireMessagesWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[PrivateMessageResponse]:
    """发送私聊消息"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_msg_send")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if player_uuid == body.receiver_id:
        raise_player_error(
            PlayerErrorCodes.CANNOT_FRIEND_SELF,
            "不能给自己发送消息",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 检查好友关系
    friend_repo = FriendRepository(db)
    if not await friend_repo.are_friends(player_uuid, body.receiver_id):
        raise_player_error(
            PlayerErrorCodes.NOT_FRIENDS,
            "非好友关系不能发送私聊",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # 发送消息
    message_repo = PrivateMessageRepository(db)
    message = await message_repo.send_message(
        sender_id=player_uuid,
        receiver_id=body.receiver_id,
        content=body.content,
    )

    record_private_message_sent(
        sender_id=str(player_uuid),
        receiver_id=str(body.receiver_id),
    )

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_PRIVATE_MESSAGE_SEND,
        resource_type=RESOURCE_PRIVATE_MESSAGE,
        resource_id=message.message_id,
        request_payload_jsonb={
            "receiver_id": str(body.receiver_id),
            "content_length": len(body.content),
        },
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=PrivateMessageResponse.model_validate(message),
        trace_id=trace_id,
    )


@router.get(
    "/player/messages/conversations",
    responses={
        401: {"description": "Unauthorized"},
    },
    tags=["messages"],
)
async def get_recent_conversations(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: UserPayload = RequireMessagesReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[ConversationListResponse]:
    """获取最近对话列表"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_conv_list")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    message_repo = PrivateMessageRepository(db)
    conversations = await message_repo.get_recent_conversations(player_uuid, limit)

    conv_responses = []
    for conv in conversations:
        conv_responses.append(
            ConversationResponse(
                friend_id=conv["friend_id"],
                latest_message=PrivateMessageResponse.model_validate(conv["latest_message"])
                if conv["latest_message"]
                else None,
            )
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=ConversationListResponse(conversations=conv_responses),
        trace_id=trace_id,
    )


@router.get(
    "/player/messages/conversations/{friend_id}",
    responses={
        401: {"description": "Unauthorized"},
    },
    tags=["messages"],
)
async def get_conversation(
    friend_id: uuid.UUID,
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireMessagesReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[MessageListResponse]:
    """获取与指定好友的对话"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_conv_get")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    message_repo = PrivateMessageRepository(db)
    messages = await message_repo.get_conversation(player_uuid, friend_id, limit, offset)

    return EnvelopeResponse(
        request_id=request_id,
        data=MessageListResponse(
            messages=[PrivateMessageResponse.model_validate(m) for m in messages]
        ),
        trace_id=trace_id,
    )


@router.post(
    "/player/messages/{message_id}/read",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Message not found"},
    },
    tags=["messages"],
)
async def mark_message_read(
    message_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireMessagesWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[PrivateMessageResponse]:
    """标记消息已读"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_msg_read")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    message_repo = PrivateMessageRepository(db)
    success = await message_repo.mark_as_read(message_id, player_uuid)

    if not success:
        raise_player_error(
            PlayerErrorCodes.MESSAGE_NOT_FOUND,
            "消息不存在或无权标记",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    record_private_message_read(receiver_id=str(player_uuid))

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_PRIVATE_MESSAGE_READ,
        resource_type=RESOURCE_PRIVATE_MESSAGE,
        resource_id=message_id,
        result_status=200,
    )

    message = await message_repo.get_message_by_id(message_id)
    return EnvelopeResponse(
        request_id=request_id,
        data=PrivateMessageResponse.model_validate(message),
        trace_id=trace_id,
    )


@router.get(
    "/player/messages/unread",
    responses={
        401: {"description": "Unauthorized"},
    },
    tags=["messages"],
)
async def get_unread_messages(
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    current_user: UserPayload = RequireMessagesReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[MessageListResponse]:
    """获取未读消息列表"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_unread_list")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    message_repo = PrivateMessageRepository(db)
    messages = await message_repo.get_unread_messages(player_uuid, limit)

    return EnvelopeResponse(
        request_id=request_id,
        data=MessageListResponse(
            messages=[PrivateMessageResponse.model_validate(m) for m in messages]
        ),
        trace_id=trace_id,
    )


@router.get(
    "/player/messages/unread/count",
    responses={
        401: {"description": "Unauthorized"},
    },
    tags=["messages"],
)
async def get_unread_count(
    request: Request,
    current_user: UserPayload = RequireMessagesReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[UnreadCountResponse]:
    """获取未读消息数"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_unread_cnt")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    message_repo = PrivateMessageRepository(db)
    count = await message_repo.get_unread_count(player_uuid)

    return EnvelopeResponse(
        request_id=request_id,
        data=UnreadCountResponse(unread_count=count),
        trace_id=trace_id,
    )
