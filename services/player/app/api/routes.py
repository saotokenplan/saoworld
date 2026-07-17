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
    RequireGuildReadScope,
    RequireGuildWriteScope,
    RequireOpsAchievementsWriteScope,
    RequireOpsRole,
    RequirePlayerRole,
    RequireQuestsReadScope,
    RequireQuestsWriteScope,
    RequireSocialReadScope,
    RequireGuildWarReadScope,
    RequireGuildWarWriteScope,
    RequireCollabQuestReadScope,
    RequireCollabQuestWriteScope,
    RequireEconomyReadScope,
    RequireMatchReadScope,
    RequireMatchWriteScope,
    RequireMatchOpsScope,
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
    record_guild_created,
    record_guild_member_added,
    record_guild_member_removed,
    record_guild_message_sent,
    record_guild_message_read,
    record_quest_accept,
    record_quest_complete,
    record_quest_fail,
    record_quest_progress_update,
    record_reputation_add,
    record_reputation_remove,
    record_reputation_unlock,
    record_equipment_equip,
    record_equipment_unequip,
    record_guild_war_declared,
    record_guild_war_completed,
    record_guild_war_participant_joined,
    record_collab_quest_created,
    record_collab_quest_completed,
    record_match_queue_joined,
    record_match_queue_left,
    record_match_result_submitted,
    record_match_rating_change,
    record_match_leaderboard_query,
    record_match_player_rank_query,
    record_match_tier_distribution_query,
    record_match_season_settlement,
    record_match_season_reward_grant,
    set_match_season_active_players,
    set_match_tier_distribution,
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
    ACTION_PRIVATE_MESSAGE_DELETE,
    ACTION_GUILD_CREATE,
    ACTION_GUILD_UPDATE,
    ACTION_GUILD_DELETE,
    ACTION_GUILD_MEMBER_ADD,
    ACTION_GUILD_MEMBER_REMOVE,
    ACTION_GUILD_MEMBER_LEAVE,
    ACTION_GUILD_TRANSFER_LEADER,
    ACTION_GUILD_MESSAGE_SEND,
    ACTION_GUILD_MESSAGE_READ,
    ACTION_GUILD_MESSAGE_DELETE,
    ACTION_EQUIPMENT_EQUIP,
    ACTION_EQUIPMENT_UNEQUIP,
    ACTION_GUILD_WAR_DECLARE,
    ACTION_GUILD_WAR_ACCEPT,
    ACTION_GUILD_WAR_CANCEL,
    ACTION_GUILD_WAR_COMPLETE,
    ACTION_GUILD_WAR_JOIN,
    ACTION_COLLAB_QUEST_CREATE,
    ACTION_COLLAB_QUEST_ACCEPT,
    ACTION_COLLAB_QUEST_REJECT,
    ACTION_COLLAB_QUEST_PROGRESS,
    ACTION_COLLAB_QUEST_COMPLETE,
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
    RESOURCE_GUILD,
    RESOURCE_GUILD_MEMBER,
    RESOURCE_GUILD_MESSAGE,
    RESOURCE_EQUIPMENT,
    RESOURCE_GUILD_WAR,
    RESOURCE_GUILD_WAR_PARTICIPANT,
    RESOURCE_COLLAB_QUEST,
    RESOURCE_ECONOMY,
    RESOURCE_MATCH_SEASON,
    RESOURCE_MATCH_QUEUE,
    RESOURCE_MATCH_ROOM,
    RESOURCE_MATCH_RESULT,
    RESOURCE_PLAYER_RATING,
    RESOURCE_MATCH_SEASON_REWARD,
    ACTION_ECONOMY_OVERVIEW_QUERY,
    ACTION_ECONOMY_TRADE_STATS_QUERY,
    ACTION_ECONOMY_AUCTION_STATS_QUERY,
    ACTION_ECONOMY_WALLET_STATS_QUERY,
    ACTION_ECONOMY_TRENDS_QUERY,
    ACTION_ECONOMY_TOP_TRADERS_QUERY,
    ACTION_MATCH_QUEUE_JOIN,
    ACTION_MATCH_QUEUE_LEAVE,
    ACTION_MATCH_ROOM_READY,
    ACTION_MATCH_RESULT_SUBMIT,
    ACTION_MATCH_SEASON_CREATE,
    ACTION_MATCH_SEASON_STATUS_UPDATE,
    ACTION_MATCH_RATING_QUERY,
    ACTION_MATCH_HISTORY_QUERY,
    ACTION_MATCH_LEADERBOARD_QUERY,
    ACTION_MATCH_RANK_QUERY,
    ACTION_MATCH_TIER_DISTRIBUTION_QUERY,
    ACTION_MATCH_NEIGHBORS_QUERY,
    ACTION_MATCH_SEASON_SETTLE,
    ACTION_MATCH_REWARD_QUERY,
    ACTION_MATCH_REWARD_GRANT,
    AuditRepository,
)
from app.repositories.achievement_repo import (
    AchievementDefinitionRepository,
    PlayerAchievementRepository,
)
from app.repositories.contribution_repo import ContributionRepository
from app.repositories.friend_repo import FriendRepository
from app.repositories.guild_repo import GuildRepository
from app.repositories.guild_message_repo import GuildMessageRepository
from app.repositories.guild_quest_repo import GuildQuestRepository, GuildQuestProgressRepository
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.equipment_repo import EquipmentRepository
from app.repositories.private_message_repo import PrivateMessageRepository
from app.repositories.player_quest_repo import PlayerQuestRepository
from app.repositories.player_region_repo import PlayerRegionRepository
from app.repositories.player_repo import PlayerRepository
from app.repositories.trade_repo import TradeRepository
from app.repositories.auction_repo import AuctionRepository
from app.repositories.wallet_repo import WalletRepository
from app.repositories.guild_war_repo import GuildWarRepository
from app.repositories.friend_collab_quest_repo import FriendCollabQuestRepository
from app.repositories.economic_repo import EconomicRepository
from app.repositories.match_repo import (
    MatchSeasonRepository,
    PlayerRatingRepository,
    MatchQueueRepository,
    MatchRoomRepository,
    MatchResultRepository,
    calculate_rating_change,
)
from app.repositories.season_reward_repo import SeasonRewardRepository
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
    CreateGuildRequest,
    UpdateGuildRequest,
    AddGuildMemberRequest,
    TransferLeaderRequest,
    GuildResponse,
    GuildMemberResponse,
    GuildMemberListItemResponse,
    GuildMemberListResponse,
    SendGuildMessageRequest,
    GuildMessageResponse,
    GuildMessageListResponse,
    SocialOverview,
    GuildSummary,
    FriendSummary,
    GuildQuestResponse,
    GuildQuestProgressResponse,
    CreateGuildQuestRequest,
    UpdateGuildQuestProgressRequest,
    GuildQuestListResponse,
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
    EquipmentResponse,
    EquipItemRequest,
    UnequipItemRequest,
    EquipmentStatsResponse,
    get_reputation_level,
    REPUTATION_LEVEL_THRESHOLDS,
    CreateTradeRequest,
    TradeResponse,
    TradeListResponse,
    AuctionStatus,
    CreateAuctionRequest,
    AuctionResponse,
    AuctionListResponse,
    BidRequest,
    WalletResponse,
    WalletTransactionResponse,
    WalletTransactionListResponse,
    GuildWarResponse,
    GuildWarListResponse,
    GuildWarParticipantResponse,
    WarScoreboardResponse,
    DeclareWarRequest,
    JoinWarRequest,
    FriendCollabQuestResponse,
    FriendCollabQuestListResponse,
    CreateFriendCollabQuestRequest,
    UpdateFriendCollabQuestProgressRequest,
    EconomicOverview,
    TradeStatsItem,
    AuctionStatsItem,
    WalletStatsItem,
    EconomicTrendPoint,
    TopTraderItem,
    MatchTier,
    MatchMode,
    MatchQueueStatus,
    MatchRoomStatus,
    MatchSeasonStatus,
    PlayerRatingResponse,
    MatchQueueResponse,
    MatchRoomResponse,
    MatchResultResponse,
    MatchSeasonResponse,
    JoinMatchQueueRequest,
    LeaveMatchQueueRequest,
    SubmitMatchResultRequest,
    CreateMatchSeasonRequest,
    UpdateMatchSeasonStatusRequest,
    MatchLeaderboardItem,
    MatchLeaderboardResponse,
    PlayerRankResponse,
    TierDistributionItem,
    TierDistributionResponse,
    LeaderboardNeighborsResponse,
    SeasonRewardItem,
    SeasonRewardListResponse,
    SettleSeasonRequest,
    SeasonSettlementResponse,
)

router = APIRouter()
ops_router = APIRouter()


def _make_request_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _get_trace_id(request: Request) -> str:
    trace_id = request.headers.get("X-Trace-Id")
    if trace_id is None:
        trace_id = f"trace_{uuid.uuid4().hex[:12]}"
    return trace_id


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


@router.delete(
    "/player/messages/{message_id}",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Message not found"},
    },
    tags=["messages"],
)
async def delete_private_message(
    message_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireMessagesWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse:
    """删除私聊消息（仅发送者可删）"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_msg_del")

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
    deleted = await message_repo.delete_message(message_id, player_uuid)

    if not deleted:
        raise_player_error(
            PlayerErrorCodes.MESSAGE_NOT_FOUND,
            "消息不存在或无权删除",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_PRIVATE_MESSAGE_DELETE,
        resource_type=RESOURCE_PRIVATE_MESSAGE,
        resource_id=message_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data={"deleted": True},
        trace_id=trace_id,
    )


# === 公会相关 API ===


@router.post(
    "/player/guilds",
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Unauthorized"},
        409: {"description": "Guild name already exists or player already in guild"},
    },
    tags=["guilds"],
)
async def create_guild(
    request: Request,
    body: CreateGuildRequest,
    current_user: UserPayload = RequireGuildWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildResponse]:
    """创建公会"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_create")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    audit_repo = AuditRepository(db)

    # 检查玩家是否已加入公会
    existing_guild = await guild_repo.get_guild_by_player(player_uuid)
    if existing_guild is not None:
        raise_player_error(
            PlayerErrorCodes.ALREADY_IN_GUILD,
            "您已加入公会，无法创建新公会",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    # 检查公会名称是否存在
    existing_name = await guild_repo.get_guild_by_name(body.name)
    if existing_name is not None:
        raise_player_error(
            PlayerErrorCodes.GUILD_NAME_EXISTS,
            "公会名称已存在",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    # 创建公会
    guild = await guild_repo.create_guild(
        name=body.name,
        leader_id=player_uuid,
        description=body.description,
        max_members=body.max_members,
    )

    # 记录审计日志
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role="player",
        action=ACTION_GUILD_CREATE,
        resource_type=RESOURCE_GUILD,
        resource_id=guild.guild_id,
        request_payload_jsonb={"name": body.name},
        result_status=201,
    )

    # 记录指标
    record_guild_created(current_user.user_id)

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildResponse.model_validate(guild),
        trace_id=trace_id,
    )


@router.get(
    "/player/guilds/my",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Not in guild"},
    },
    tags=["guilds"],
)
async def get_my_guild(
    request: Request,
    current_user: UserPayload = RequireGuildReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildResponse]:
    """获取我的公会"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_my")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    guild = await guild_repo.get_guild_by_player(player_uuid)

    if guild is None:
        raise_player_error(
            PlayerErrorCodes.NOT_IN_GUILD,
            "您未加入任何公会",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildResponse.model_validate(guild),
        trace_id=trace_id,
    )


@router.get(
    "/player/guilds/{guild_id}",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Guild not found"},
    },
    tags=["guilds"],
)
async def get_guild(
    request: Request,
    guild_id: uuid.UUID,
    current_user: UserPayload = RequireGuildReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildResponse]:
    """获取公会详情"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_get")

    guild_repo = GuildRepository(db)
    guild = await guild_repo.get_guild_by_id(guild_id)

    if guild is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_NOT_FOUND,
            "公会不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildResponse.model_validate(guild),
        trace_id=trace_id,
    )


@router.put(
    "/player/guilds/{guild_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not guild leader"},
        404: {"description": "Guild not found"},
    },
    tags=["guilds"],
)
async def update_guild(
    request: Request,
    guild_id: uuid.UUID,
    body: UpdateGuildRequest,
    current_user: UserPayload = RequireGuildWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildResponse]:
    """更新公会信息（仅会长）"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_update")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    audit_repo = AuditRepository(db)

    # 检查是否为会长
    if not await guild_repo.is_guild_leader(guild_id, player_uuid):
        raise_player_error(
            PlayerErrorCodes.NOT_GUILD_LEADER,
            "只有会长可以更新公会信息",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # 更新公会
    guild = await guild_repo.update_guild(
        guild_id=guild_id,
        description=body.description,
        announcement=body.announcement,
    )

    if guild is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_NOT_FOUND,
            "公会不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # 记录审计日志
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role="player",
        action=ACTION_GUILD_UPDATE,
        resource_type=RESOURCE_GUILD,
        resource_id=guild.guild_id,
        request_payload_jsonb={"description": body.description, "announcement": body.announcement},
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildResponse.model_validate(guild),
        trace_id=trace_id,
    )


@router.delete(
    "/player/guilds/{guild_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not guild leader"},
        404: {"description": "Guild not found"},
    },
    tags=["guilds"],
)
async def delete_guild(
    request: Request,
    guild_id: uuid.UUID,
    current_user: UserPayload = RequireGuildWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[dict]:
    """解散公会（仅会长）"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_delete")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    audit_repo = AuditRepository(db)

    # 检查公会是否存在
    guild = await guild_repo.get_guild_by_id(guild_id)
    if guild is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_NOT_FOUND,
            "公会不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # 检查是否为会长
    if not await guild_repo.is_guild_leader(guild_id, player_uuid):
        raise_player_error(
            PlayerErrorCodes.NOT_GUILD_LEADER,
            "只有会长可以解散公会",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # 删除公会
    await guild_repo.delete_guild(guild_id)

    # 记录审计日志
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role="player",
        action=ACTION_GUILD_DELETE,
        resource_type=RESOURCE_GUILD,
        resource_id=guild_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data={"deleted": True},
        trace_id=trace_id,
    )


@router.post(
    "/player/guilds/{guild_id}/members",
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not guild officer"},
        404: {"description": "Guild not found"},
        409: {"description": "Player already in guild or guild full"},
    },
    tags=["guilds"],
)
async def add_guild_member(
    request: Request,
    guild_id: uuid.UUID,
    body: AddGuildMemberRequest,
    current_user: UserPayload = RequireGuildWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildMemberResponse]:
    """邀请成员加入公会（会长/官员）"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_member_add")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    audit_repo = AuditRepository(db)

    # 检查公会是否存在
    guild = await guild_repo.get_guild_by_id(guild_id)
    if guild is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_NOT_FOUND,
            "公会不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # 检查是否为公会官员
    if not await guild_repo.is_guild_officer(guild_id, player_uuid):
        raise_player_error(
            PlayerErrorCodes.NOT_GUILD_OFFICER,
            "只有会长或官员可以邀请成员",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # 添加成员
    member = await guild_repo.add_member(guild_id, body.player_id)
    if member is None:
        # 检查是公会已满还是玩家已在公会
        target_guild = await guild_repo.get_guild_by_player(body.player_id)
        if target_guild is not None:
            raise_player_error(
                PlayerErrorCodes.ALREADY_IN_GUILD,
                "该玩家已加入其他公会",
                request_id,
                status_code=status.HTTP_409_CONFLICT,
            )
        raise_player_error(
            PlayerErrorCodes.GUILD_FULL,
            "公会成员已满",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    # 记录审计日志
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role="player",
        action=ACTION_GUILD_MEMBER_ADD,
        resource_type=RESOURCE_GUILD_MEMBER,
        resource_id=member.guild_member_id,
        request_payload_jsonb={"player_id": str(body.player_id)},
        result_status=201,
    )

    # 记录指标
    record_guild_member_added(str(guild_id))

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildMemberResponse.model_validate(member),
        trace_id=trace_id,
    )


@router.delete(
    "/player/guilds/{guild_id}/members/{player_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not guild officer or cannot remove leader"},
        404: {"description": "Guild or member not found"},
    },
    tags=["guilds"],
)
async def remove_guild_member(
    request: Request,
    guild_id: uuid.UUID,
    player_id: uuid.UUID,
    current_user: UserPayload = RequireGuildWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[dict]:
    """移除公会成员（会长/官员）"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_member_remove")

    try:
        operator_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    audit_repo = AuditRepository(db)

    # 检查公会是否存在
    guild = await guild_repo.get_guild_by_id(guild_id)
    if guild is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_NOT_FOUND,
            "公会不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # 检查是否为公会官员
    if not await guild_repo.is_guild_officer(guild_id, operator_uuid):
        raise_player_error(
            PlayerErrorCodes.NOT_GUILD_OFFICER,
            "只有会长或官员可以移除成员",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # 移除成员
    success = await guild_repo.remove_member(guild_id, player_id)
    if not success:
        member = await guild_repo.get_member(guild_id, player_id)
        if member is None:
            raise_player_error(
                PlayerErrorCodes.NOT_IN_GUILD,
                "该玩家不是公会成员",
                request_id,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        raise_player_error(
            PlayerErrorCodes.CANNOT_REMOVE_LEADER,
            "不能移除会长",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # 记录审计日志
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role="player",
        action=ACTION_GUILD_MEMBER_REMOVE,
        resource_type=RESOURCE_GUILD_MEMBER,
        resource_id=player_id,
        request_payload_jsonb={"player_id": str(player_id)},
        result_status=200,
    )

    # 记录指标
    record_guild_member_removed(str(guild_id))

    return EnvelopeResponse(
        request_id=request_id,
        data={"removed": True},
        trace_id=trace_id,
    )


@router.post(
    "/player/guilds/{guild_id}/leave",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Cannot leave as leader"},
        404: {"description": "Not in guild"},
    },
    tags=["guilds"],
)
async def leave_guild(
    request: Request,
    guild_id: uuid.UUID,
    current_user: UserPayload = RequireGuildWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[dict]:
    """退出公会"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_leave")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    audit_repo = AuditRepository(db)

    # 检查公会是否存在
    guild = await guild_repo.get_guild_by_id(guild_id)
    if guild is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_NOT_FOUND,
            "公会不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # 检查是否为会长
    if await guild_repo.is_guild_leader(guild_id, player_uuid):
        raise_player_error(
            PlayerErrorCodes.CANNOT_LEAVE_AS_LEADER,
            "会长不能直接退出公会，请先转让会长或解散公会",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # 退出公会
    success = await guild_repo.remove_member(guild_id, player_uuid)
    if not success:
        raise_player_error(
            PlayerErrorCodes.NOT_IN_GUILD,
            "您不是该公会成员",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # 记录审计日志
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role="player",
        action=ACTION_GUILD_MEMBER_LEAVE,
        resource_type=RESOURCE_GUILD_MEMBER,
        resource_id=player_uuid,
        result_status=200,
    )

    # 记录指标
    record_guild_member_removed(str(guild_id))

    return EnvelopeResponse(
        request_id=request_id,
        data={"left": True},
        trace_id=trace_id,
    )


@router.post(
    "/player/guilds/{guild_id}/transfer",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not guild leader"},
        404: {"description": "Guild or member not found"},
    },
    tags=["guilds"],
)
async def transfer_guild_leader(
    request: Request,
    guild_id: uuid.UUID,
    body: TransferLeaderRequest,
    current_user: UserPayload = RequireGuildWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[dict]:
    """转让会长"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_transfer")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    audit_repo = AuditRepository(db)

    # 检查是否为会长
    if not await guild_repo.is_guild_leader(guild_id, player_uuid):
        raise_player_error(
            PlayerErrorCodes.NOT_GUILD_LEADER,
            "只有会长可以转让会长",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # 转让会长
    success = await guild_repo.transfer_leader(guild_id, body.new_leader_id)
    if not success:
        raise_player_error(
            PlayerErrorCodes.NOT_IN_GUILD,
            "新会长必须是本公会成员",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # 记录审计日志
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role="player",
        action=ACTION_GUILD_TRANSFER_LEADER,
        resource_type=RESOURCE_GUILD,
        resource_id=guild_id,
        request_payload_jsonb={"new_leader_id": str(body.new_leader_id)},
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data={"transferred": True},
        trace_id=trace_id,
    )


@router.get(
    "/player/guilds/{guild_id}/members",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Guild not found"},
    },
    tags=["guilds"],
)
async def get_guild_members(
    request: Request,
    guild_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireGuildReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildMemberListResponse]:
    """获取公会成员列表"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_members")

    guild_repo = GuildRepository(db)
    player_repo = PlayerRepository(db)

    # 检查公会是否存在
    guild = await guild_repo.get_guild_by_id(guild_id)
    if guild is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_NOT_FOUND,
            "公会不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # 获取成员列表
    members, total = await guild_repo.get_members(guild_id, limit, offset)

    # 查询玩家信息
    member_items = []
    for member in members:
        player = await player_repo.get_player_by_id(member.player_id)
        member_items.append(
            GuildMemberListItemResponse(
                guild_member_id=member.guild_member_id,
                player_id=member.player_id,
                player_display_name=player.display_name if player else "",
                player_level=player.level if player else 1,
                role=member.role,
                joined_at=member.joined_at,
            )
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildMemberListResponse(members=member_items, total=total),
        trace_id=trace_id,
    )


# === 公会消息 API ===


@router.post(
    "/player/guilds/{guild_id}/messages",
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not in guild"},
        404: {"description": "Guild not found"},
        400: {"description": "Message empty or too long"},
    },
    tags=["guilds"],
)
async def send_guild_message(
    request: Request,
    guild_id: uuid.UUID,
    body: SendGuildMessageRequest,
    current_user: UserPayload = RequireGuildWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildMessageResponse]:
    """发送公会消息"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_msg_send")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    message_repo = GuildMessageRepository(db)
    audit_repo = AuditRepository(db)

    guild = await guild_repo.get_guild_by_id(guild_id)
    if guild is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_NOT_FOUND,
            "公会不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    guild_member = await guild_repo.get_member(guild_id, player_uuid)
    if guild_member is None:
        raise_player_error(
            PlayerErrorCodes.NOT_IN_GUILD,
            "您不是该公会成员，无法发送消息",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    message = await message_repo.send_message(
        guild_id=guild_id,
        sender_id=player_uuid,
        content=body.content,
    )

    record_guild_message_sent(guild_id=str(guild_id), sender_id=str(player_uuid))

    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role="player",
        action=ACTION_GUILD_MESSAGE_SEND,
        resource_type=RESOURCE_GUILD_MESSAGE,
        resource_id=message.message_id,
        request_payload_jsonb={"content_length": len(body.content)},
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildMessageResponse.model_validate(message),
        trace_id=trace_id,
    )


@router.get(
    "/player/guilds/{guild_id}/messages",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not in guild"},
        404: {"description": "Guild not found"},
    },
    tags=["guilds"],
)
async def get_guild_messages(
    request: Request,
    guild_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireGuildReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildMessageListResponse]:
    """获取公会消息列表"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_msg_list")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    message_repo = GuildMessageRepository(db)

    guild = await guild_repo.get_guild_by_id(guild_id)
    if guild is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_NOT_FOUND,
            "公会不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    guild_member = await guild_repo.get_member(guild_id, player_uuid)
    if guild_member is None:
        raise_player_error(
            PlayerErrorCodes.NOT_IN_GUILD,
            "您不是该公会成员",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    messages, total = await message_repo.get_guild_messages(
        guild_id=guild_id,
        limit=limit,
        offset=offset,
    )

    message_responses = [GuildMessageResponse.model_validate(m) for m in messages]

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildMessageListResponse(messages=message_responses),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.post(
    "/player/guilds/{guild_id}/messages/read",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not in guild"},
        404: {"description": "Guild not found"},
    },
    tags=["guilds"],
)
async def mark_guild_messages_read(
    request: Request,
    guild_id: uuid.UUID,
    current_user: UserPayload = RequireGuildReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[dict]:
    """标记公会消息已读"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_msg_read")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    message_repo = GuildMessageRepository(db)
    audit_repo = AuditRepository(db)

    guild = await guild_repo.get_guild_by_id(guild_id)
    if guild is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_NOT_FOUND,
            "公会不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    guild_member = await guild_repo.get_member(guild_id, player_uuid)
    if guild_member is None:
        raise_player_error(
            PlayerErrorCodes.NOT_IN_GUILD,
            "您不是该公会成员",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    updated_count = await message_repo.mark_messages_as_read(guild_id, player_uuid)

    record_guild_message_read(guild_id=str(guild_id), player_id=str(player_uuid))

    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role="player",
        action=ACTION_GUILD_MESSAGE_READ,
        resource_type=RESOURCE_GUILD_MESSAGE,
        resource_id=None,
        request_payload_jsonb={"updated_count": updated_count},
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data={"marked_read": updated_count},
        trace_id=trace_id,
    )


@router.get(
    "/player/guilds/{guild_id}/messages/unread-count",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not in guild"},
        404: {"description": "Guild not found"},
    },
    tags=["guilds"],
)
async def get_guild_unread_count(
    request: Request,
    guild_id: uuid.UUID,
    current_user: UserPayload = RequireGuildReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[UnreadCountResponse]:
    """获取公会未读消息数"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_msg_unread")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    message_repo = GuildMessageRepository(db)

    guild = await guild_repo.get_guild_by_id(guild_id)
    if guild is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_NOT_FOUND,
            "公会不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    guild_member = await guild_repo.get_member(guild_id, player_uuid)
    if guild_member is None:
        raise_player_error(
            PlayerErrorCodes.NOT_IN_GUILD,
            "您不是该公会成员",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    unread_count = await message_repo.get_unread_count(guild_id, player_uuid)

    return EnvelopeResponse(
        request_id=request_id,
        data=UnreadCountResponse(unread_count=unread_count),
        trace_id=trace_id,
    )


@router.delete(
    "/player/guilds/{guild_id}/messages/{message_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Cannot delete other's message"},
        404: {"description": "Message not found"},
    },
    tags=["guilds"],
)
async def delete_guild_message(
    request: Request,
    guild_id: uuid.UUID,
    message_id: uuid.UUID,
    current_user: UserPayload = RequireGuildWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[dict]:
    """删除公会消息（发送者或会长/官员）"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_msg_delete")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    message_repo = GuildMessageRepository(db)
    audit_repo = AuditRepository(db)

    guild = await guild_repo.get_guild_by_id(guild_id)
    if guild is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_NOT_FOUND,
            "公会不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    guild_member = await guild_repo.get_member(guild_id, player_uuid)
    if guild_member is None:
        raise_player_error(
            PlayerErrorCodes.NOT_IN_GUILD,
            "您不是该公会成员",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    is_leader_or_officer = await guild_repo.is_guild_officer(guild_id, player_uuid)

    deleted = await message_repo.delete_message(
        guild_id=guild_id,
        message_id=message_id,
        player_id=player_uuid,
        is_leader_or_officer=is_leader_or_officer,
    )

    if not deleted:
        message = await message_repo.get_message_by_id(guild_id, message_id)
        if message is None:
            raise_player_error(
                PlayerErrorCodes.MESSAGE_NOT_FOUND,
                "消息不存在",
                request_id,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        raise_player_error(
            PlayerErrorCodes.CANNOT_DELETE_OTHER_MESSAGE,
            "只能删除自己发送的消息",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role="player",
        action=ACTION_GUILD_MESSAGE_DELETE,
        resource_type=RESOURCE_GUILD_MESSAGE,
        resource_id=message_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data={"deleted": True},
        trace_id=trace_id,
    )


# === 社交数据聚合 API ===


@router.get(
    "/player/social/overview",
    responses={
        401: {"description": "Unauthorized"},
    },
    tags=["social"],
)
async def get_social_overview(
    request: Request,
    current_user: UserPayload = RequireSocialReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[SocialOverview]:
    """获取社交概览数据（好友数、未读消息、公会信息、最近好友）"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_social_overview")

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
    message_repo = PrivateMessageRepository(db)
    guild_repo = GuildRepository(db)
    player_repo = PlayerRepository(db)

    # 1. 获取好友总数
    friends, friends_total = await friend_repo.get_friends(
        player_uuid, limit=1000, offset=0
    )

    # 2. 获取待处理好友请求数
    pending_requests, pending_total = await friend_repo.get_pending_requests(
        player_uuid, limit=1000, offset=0
    )

    # 3. 获取未读消息数
    unread_count = await message_repo.get_unread_count(player_uuid)

    # 4. 获取公会信息
    guild_member = await guild_repo.get_guild_member_by_player(player_uuid)
    guild_info: GuildSummary | None = None
    if guild_member:
        guild = await guild_repo.get_guild_by_id(guild_member.guild_id)
        if guild:
            guild_info = GuildSummary(
                guild_id=guild.guild_id,
                name=guild.name,
                level=guild.level,
                member_count=guild.member_count,
                my_role=guild_member.role,
            )

    # 5. 获取最近好友列表（最多5个）
    recent_friends: list[FriendSummary] = []
    if friends:
        # 按创建时间倒序，取前5个
        recent_friends_data = sorted(
            friends, key=lambda f: f.created_at, reverse=True
        )[:5]
        for friendship in recent_friends_data:
            friend_player = await player_repo.get_player_by_id(friendship.friend_id)
            if friend_player:
                recent_friends.append(
                    FriendSummary(
                        player_id=friendship.friend_id,
                        player_name=friend_player.display_name,
                        level=friend_player.level,
                        online=False,  # 在线状态暂时硬编码为 False
                    )
                )

    return EnvelopeResponse(
        request_id=request_id,
        data=SocialOverview(
            friends_count=friends_total,
            pending_requests=pending_total,
            unread_messages=unread_count,
            guild_info=guild_info,
            recent_friends=recent_friends,
        ),
        trace_id=trace_id,
    )


# === 装备系统 API ===


@router.get(
    "/player/equipment",
    responses={
        401: {"description": "Unauthorized"},
        400: {"description": "Invalid player ID"},
    },
    tags=["equipment"],
)
async def get_player_equipment(
    request: Request,
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[EquipmentResponse]]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_player_equipment")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    repo = EquipmentRepository(db)
    equipment = await repo.get_equipment(player_uuid)

    equipment_responses = [EquipmentResponse.model_validate(e) for e in equipment]

    return EnvelopeResponse(
        request_id=request_id,
        data=equipment_responses,
        trace_id=trace_id,
    )


@router.get(
    "/player/equipment/stats",
    responses={
        401: {"description": "Unauthorized"},
        400: {"description": "Invalid player ID"},
    },
    tags=["equipment"],
)
async def get_equipment_stats(
    request: Request,
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[EquipmentStatsResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_equipment_stats")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    repo = EquipmentRepository(db)
    stats = await repo.get_equipment_stats(player_uuid)

    return EnvelopeResponse(
        request_id=request_id,
        data=EquipmentStatsResponse(stats=stats),
        trace_id=trace_id,
    )


@router.post(
    "/player/equipment/equip",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized"},
        400: {"description": "Invalid request"},
        404: {"description": "Item not found"},
        409: {"description": "Slot occupied or cannot equip"},
    },
    tags=["equipment"],
)
async def equip_item(
    body: EquipItemRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[EquipmentResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_equip_item")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    repo = EquipmentRepository(db)
    equipment = await repo.equip_item(
        player_id=player_uuid,
        item_key=body.item_key,
        slot=body.slot.value,
        item_stats=body.item_stats,
    )

    record_equipment_equip()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_EQUIPMENT_EQUIP,
        resource_type=RESOURCE_EQUIPMENT,
        resource_id=equipment.equipment_id,
        request_payload_jsonb={
            "item_key": body.item_key,
            "slot": body.slot.value,
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=EquipmentResponse.model_validate(equipment),
        trace_id=trace_id,
    )


@router.post(
    "/player/equipment/unequip",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized"},
        400: {"description": "Invalid request"},
        409: {"description": "Slot is empty"},
    },
    tags=["equipment"],
)
async def unequip_item(
    body: UnequipItemRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[EquipmentResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_unequip_item")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    repo = EquipmentRepository(db)
    equipment = await repo.unequip_item(
        player_id=player_uuid,
        slot=body.slot.value,
    )

    record_equipment_unequip()

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_EQUIPMENT_UNEQUIP,
        resource_type=RESOURCE_EQUIPMENT,
        resource_id=equipment.equipment_id,
        request_payload_jsonb={
            "slot": body.slot.value,
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=EquipmentResponse.model_validate(equipment),
        trace_id=trace_id,
    )


# === 公会任务 API ===


@router.get(
    "/player/guilds/{guild_id}/quests",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not in guild"},
        404: {"description": "Guild not found"},
    },
    tags=["guilds"],
)
async def get_guild_quests(
    request: Request,
    guild_id: uuid.UUID,
    quest_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireGuildReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildQuestListResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_quests")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    quest_repo = GuildQuestRepository(db)

    guild = await guild_repo.get_guild_by_id(guild_id)
    if guild is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_NOT_FOUND,
            "公会不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    guild_member = await guild_repo.get_member(guild_id, player_uuid)
    if guild_member is None:
        raise_player_error(
            PlayerErrorCodes.NOT_IN_GUILD,
            "您不是该公会成员",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    quests, total = await quest_repo.get_guild_quests(guild_id, status=quest_status, limit=limit, offset=offset)

    quest_responses = [GuildQuestResponse.model_validate(q) for q in quests]

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildQuestListResponse(quests=quest_responses, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.post(
    "/player/guilds/{guild_id}/quests",
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not guild officer"},
        404: {"description": "Guild not found"},
        409: {"description": "Quest key already exists"},
    },
    tags=["guilds"],
)
async def create_guild_quest(
    request: Request,
    guild_id: uuid.UUID,
    body: CreateGuildQuestRequest,
    current_user: UserPayload = RequireGuildWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildQuestResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_quest_create")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    quest_repo = GuildQuestRepository(db)
    audit_repo = AuditRepository(db)

    guild = await guild_repo.get_guild_by_id(guild_id)
    if guild is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_NOT_FOUND,
            "公会不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if not await guild_repo.is_guild_leader(guild_id, player_uuid):
        raise_player_error(
            PlayerErrorCodes.NOT_GUILD_LEADER,
            "只有会长可以创建公会任务",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    existing = await quest_repo.get_quest_by_key(guild_id, body.quest_key)
    if existing is not None:
        raise_player_error(
            PlayerErrorCodes.GUILD_QUEST_KEY_EXISTS,
            "任务键名已存在",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    quest = await quest_repo.create_quest(
        guild_id=guild_id,
        quest_key=body.quest_key,
        name=body.name,
        description=body.description,
        quest_type=body.quest_type.value,
        objectives_jsonb=body.objectives,
        rewards_jsonb=body.rewards,
        progress_target=body.progress_target,
        time_limit_minutes=body.time_limit_minutes,
        created_by=player_uuid,
    )

    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action="GUILD_QUEST_CREATE",
        resource_type="GUILD_QUEST",
        resource_id=quest.guild_quest_id,
        request_payload_jsonb=body.model_dump(mode="json"),
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildQuestResponse.model_validate(quest),
        trace_id=trace_id,
    )


@router.get(
    "/player/guilds/{guild_id}/quests/{guild_quest_id}",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not in guild"},
        404: {"description": "Guild or quest not found"},
    },
    tags=["guilds"],
)
async def get_guild_quest(
    request: Request,
    guild_id: uuid.UUID,
    guild_quest_id: uuid.UUID,
    current_user: UserPayload = RequireGuildReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildQuestResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_quest_get")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    quest_repo = GuildQuestRepository(db)

    guild = await guild_repo.get_guild_by_id(guild_id)
    if guild is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_NOT_FOUND,
            "公会不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    guild_member = await guild_repo.get_member(guild_id, player_uuid)
    if guild_member is None:
        raise_player_error(
            PlayerErrorCodes.NOT_IN_GUILD,
            "您不是该公会成员",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    quest = await quest_repo.get_quest_by_id(guild_quest_id)
    if quest is None or quest.guild_id != guild_id:
        raise_player_error(
            PlayerErrorCodes.GUILD_QUEST_NOT_FOUND,
            "任务不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildQuestResponse.model_validate(quest),
        trace_id=trace_id,
    )


@router.post(
    "/player/guilds/{guild_id}/quests/{guild_quest_id}/progress",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not in guild"},
        404: {"description": "Guild or quest not found"},
        409: {"description": "Quest not active"},
    },
    tags=["guilds"],
)
async def update_guild_quest_progress(
    request: Request,
    guild_id: uuid.UUID,
    guild_quest_id: uuid.UUID,
    body: UpdateGuildQuestProgressRequest,
    current_user: UserPayload = RequireGuildWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildQuestResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_quest_progress")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    quest_repo = GuildQuestRepository(db)
    progress_repo = GuildQuestProgressRepository(db)
    audit_repo = AuditRepository(db)

    guild = await guild_repo.get_guild_by_id(guild_id)
    if guild is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_NOT_FOUND,
            "公会不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    guild_member = await guild_repo.get_member(guild_id, player_uuid)
    if guild_member is None:
        raise_player_error(
            PlayerErrorCodes.NOT_IN_GUILD,
            "您不是该公会成员",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    quest = await quest_repo.get_quest_by_id(guild_quest_id)
    if quest is None or quest.guild_id != guild_id:
        raise_player_error(
            PlayerErrorCodes.GUILD_QUEST_NOT_FOUND,
            "任务不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if quest.status != "active":
        raise_player_error(
            PlayerErrorCodes.GUILD_QUEST_NOT_ACTIVE,
            "任务未处于活跃状态",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    await progress_repo.record_contribution(guild_quest_id, player_uuid, body.contribution)

    updated_quest = await quest_repo.update_progress(guild_quest_id, body.contribution)

    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action="GUILD_QUEST_PROGRESS_UPDATE",
        resource_type="GUILD_QUEST",
        resource_id=guild_quest_id,
        request_payload_jsonb={"contribution": body.contribution},
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildQuestResponse.model_validate(updated_quest),
        trace_id=trace_id,
    )


@router.get(
    "/player/guilds/{guild_id}/quests/{guild_quest_id}/progress",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not in guild"},
        404: {"description": "Guild or quest not found"},
    },
    tags=["guilds"],
)
async def get_guild_quest_progress(
    request: Request,
    guild_id: uuid.UUID,
    guild_quest_id: uuid.UUID,
    current_user: UserPayload = RequireGuildReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildQuestProgressResponse | None]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_quest_progress_get")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    quest_repo = GuildQuestRepository(db)
    progress_repo = GuildQuestProgressRepository(db)

    guild = await guild_repo.get_guild_by_id(guild_id)
    if guild is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_NOT_FOUND,
            "公会不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    guild_member = await guild_repo.get_member(guild_id, player_uuid)
    if guild_member is None:
        raise_player_error(
            PlayerErrorCodes.NOT_IN_GUILD,
            "您不是该公会成员",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    quest = await quest_repo.get_quest_by_id(guild_quest_id)
    if quest is None or quest.guild_id != guild_id:
        raise_player_error(
            PlayerErrorCodes.GUILD_QUEST_NOT_FOUND,
            "任务不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    progress = await progress_repo.get_progress(guild_quest_id, player_uuid)

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildQuestProgressResponse.model_validate(progress) if progress else None,
        trace_id=trace_id,
    )


@router.post(
    "/player/guilds/{guild_id}/quests/{guild_quest_id}/claim-reward",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not in guild"},
        404: {"description": "Guild or quest not found"},
        409: {"description": "Quest not completed or reward already claimed"},
    },
    tags=["guilds"],
)
async def claim_guild_quest_reward(
    request: Request,
    guild_id: uuid.UUID,
    guild_quest_id: uuid.UUID,
    current_user: UserPayload = RequireGuildWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildQuestProgressResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_guild_quest_claim")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    quest_repo = GuildQuestRepository(db)
    progress_repo = GuildQuestProgressRepository(db)
    audit_repo = AuditRepository(db)

    guild = await guild_repo.get_guild_by_id(guild_id)
    if guild is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_NOT_FOUND,
            "公会不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    guild_member = await guild_repo.get_member(guild_id, player_uuid)
    if guild_member is None:
        raise_player_error(
            PlayerErrorCodes.NOT_IN_GUILD,
            "您不是该公会成员",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    quest = await quest_repo.get_quest_by_id(guild_quest_id)
    if quest is None or quest.guild_id != guild_id:
        raise_player_error(
            PlayerErrorCodes.GUILD_QUEST_NOT_FOUND,
            "任务不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if quest.status != "completed":
        raise_player_error(
            PlayerErrorCodes.GUILD_QUEST_NOT_ACTIVE,
            "任务未完成，无法领取奖励",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    progress = await progress_repo.get_progress(guild_quest_id, player_uuid)
    if progress is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_QUEST_NOT_FOUND,
            "您没有参与该任务",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if progress.claimed_reward:
        raise_player_error(
            PlayerErrorCodes.GUILD_QUEST_REWARD_ALREADY_CLAIMED,
            "奖励已领取",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    progress = await progress_repo.claim_reward(guild_quest_id, player_uuid)

    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action="GUILD_QUEST_REWARD_CLAIM",
        resource_type="GUILD_QUEST",
        resource_id=guild_quest_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildQuestProgressResponse.model_validate(progress),
        trace_id=trace_id,
    )


# === 交易系统 API ===


@router.post(
    "/player/trades",
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Unauthorized"},
        400: {"description": "Invalid request"},
        404: {"description": "Recipient not found"},
        409: {"description": "Insufficient inventory/coins"},
    },
    tags=["trade"],
)
async def create_trade(
    request: Request,
    body: CreateTradeRequest,
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[TradeResponse]:
    """发起交易请求"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_trade_create")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if player_uuid == body.recipient_id:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "不能与自己交易",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    trade_repo = TradeRepository(db)
    inventory_repo = InventoryRepository(db)
    wallet_repo = WalletRepository(db)

    player_repo = PlayerRepository(db)
    recipient = await player_repo.get_player_by_id(body.recipient_id)
    if recipient is None:
        raise_player_error(
            PlayerErrorCodes.PLAYER_NOT_FOUND,
            "目标玩家不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if body.offer_items:
        for item in body.offer_items:
            has_item = await inventory_repo.has_item(player_uuid, item.item_key, item.quantity)
            if not has_item:
                raise_player_error(
                    PlayerErrorCodes.INSUFFICIENT_INVENTORY,
                    f"物品 {item.item_key} 数量不足",
                    request_id,
                    status_code=status.HTTP_409_CONFLICT,
                )

    if body.offer_coins > 0:
        wallet = await wallet_repo.get_wallet(player_uuid)
        if wallet is None or wallet.gold_coins < body.offer_coins:
            raise_player_error(
                PlayerErrorCodes.INSUFFICIENT_GOLD,
                "金币不足",
                request_id,
                status_code=status.HTTP_409_CONFLICT,
            )

    trade = await trade_repo.create_trade(
        initiator_id=player_uuid,
        recipient_id=body.recipient_id,
        offer_items=[item.model_dump() for item in body.offer_items],
        offer_coins=body.offer_coins,
        request_items=[item.model_dump() for item in body.request_items],
        request_coins=body.request_coins,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=TradeResponse.model_validate(trade),
        trace_id=trace_id,
    )


@router.post(
    "/player/trades/{trade_id}/accept",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Trade not found"},
        409: {"description": "Invalid trade state or insufficient inventory/coins"},
    },
    tags=["trade"],
)
async def accept_trade(
    trade_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[TradeResponse]:
    """接受交易"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_trade_accept")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    trade_repo = TradeRepository(db)
    trade = await trade_repo.accept_trade(trade_id, player_uuid)

    if trade is None:
        raise_player_error(
            PlayerErrorCodes.TRADE_NOT_FOUND,
            "交易不存在或无法接受",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=TradeResponse.model_validate(trade),
        trace_id=trace_id,
    )


@router.post(
    "/player/trades/{trade_id}/reject",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Trade not found"},
        409: {"description": "Not recipient of trade"},
    },
    tags=["trade"],
)
async def reject_trade(
    trade_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[TradeResponse]:
    """拒绝交易"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_trade_reject")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    trade_repo = TradeRepository(db)
    trade = await trade_repo.reject_trade(trade_id, player_uuid)

    if trade is None:
        raise_player_error(
            PlayerErrorCodes.TRADE_NOT_FOUND,
            "交易不存在或无权拒绝",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=TradeResponse.model_validate(trade),
        trace_id=trace_id,
    )


@router.post(
    "/player/trades/{trade_id}/cancel",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Trade not found"},
        409: {"description": "Not initiator or trade already completed"},
    },
    tags=["trade"],
)
async def cancel_trade(
    trade_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[TradeResponse]:
    """取消交易（仅发起方）"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_trade_cancel")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    trade_repo = TradeRepository(db)
    trade = await trade_repo.cancel_trade(trade_id, player_uuid)

    if trade is None:
        raise_player_error(
            PlayerErrorCodes.TRADE_NOT_FOUND,
            "交易不存在或无权取消",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=TradeResponse.model_validate(trade),
        trace_id=trace_id,
    )


@router.get(
    "/player/trades",
    responses={
        401: {"description": "Unauthorized"},
    },
    tags=["trade"],
)
async def get_player_trades(
    request: Request,
    trade_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[TradeListResponse]:
    """获取玩家交易列表"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_trade_list")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    trade_repo = TradeRepository(db)
    trades, total = await trade_repo.get_player_trades(player_uuid, status=trade_status, limit=limit, offset=offset)

    trade_responses = [TradeResponse.model_validate(t) for t in trades]

    return EnvelopeResponse(
        request_id=request_id,
        data=TradeListResponse(trades=trade_responses, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/player/trades/{trade_id}",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Trade not found"},
    },
    tags=["trade"],
)
async def get_trade_detail(
    trade_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[TradeResponse]:
    """获取交易详情"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_trade_detail")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    trade_repo = TradeRepository(db)
    trade = await trade_repo.get_trade(trade_id, player_uuid)

    if trade is None:
        raise_player_error(
            PlayerErrorCodes.TRADE_NOT_FOUND,
            "交易不存在或无权查看",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=TradeResponse.model_validate(trade),
        trace_id=trace_id,
    )


# === 拍卖行 API ===


@router.post(
    "/player/auction/listings",
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Unauthorized"},
        400: {"description": "Invalid request"},
        409: {"description": "Insufficient inventory"},
    },
    tags=["auction"],
)
async def create_auction_listing(
    request: Request,
    body: CreateAuctionRequest,
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[AuctionResponse]:
    """创建拍卖行挂单"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_auction_create")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    auction_repo = AuctionRepository(db)
    inventory_repo = InventoryRepository(db)

    has_item = await inventory_repo.has_item(player_uuid, body.item_key, body.quantity)
    if not has_item:
        raise_player_error(
            PlayerErrorCodes.INSUFFICIENT_INVENTORY,
            f"物品 {body.item_key} 数量不足",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    if body.buyout_price is not None and body.buyout_price < body.starting_price:
        raise_player_error(
            PlayerErrorCodes.INVALID_BUYOUT_PRICE,
            "一口价不能低于起拍价",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    listing = await auction_repo.create_listing(
        seller_id=player_uuid,
        item_key=body.item_key,
        item_type=body.item_type.value,
        quantity=body.quantity,
        starting_price=body.starting_price,
        buyout_price=body.buyout_price,
        duration_hours=body.duration_hours,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=AuctionResponse.model_validate(listing),
        trace_id=trace_id,
    )


@router.post(
    "/player/auction/listings/{listing_id}/cancel",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Listing not found"},
        409: {"description": "Not seller or listing already sold/expired"},
    },
    tags=["auction"],
)
async def cancel_auction_listing(
    listing_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[AuctionResponse]:
    """取消挂单（仅卖家）"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_auction_cancel")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    auction_repo = AuctionRepository(db)
    listing = await auction_repo.cancel_listing(listing_id, player_uuid)

    if listing is None:
        raise_player_error(
            PlayerErrorCodes.AUCTION_NOT_FOUND,
            "挂单不存在或无权取消",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=AuctionResponse.model_validate(listing),
        trace_id=trace_id,
    )


@router.post(
    "/player/auction/listings/{listing_id}/bid",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Listing not found"},
        409: {"description": "Bid too low or insufficient gold"},
    },
    tags=["auction"],
)
async def place_bid(
    listing_id: uuid.UUID,
    body: BidRequest,
    request: Request,
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[AuctionResponse]:
    """出价"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_auction_bid")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    auction_repo = AuctionRepository(db)
    wallet_repo = WalletRepository(db)

    listing = await auction_repo.get_listing_by_id(listing_id)
    if listing is None:
        raise_player_error(
            PlayerErrorCodes.AUCTION_NOT_FOUND,
            "挂单不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if listing.status != AuctionStatus.ACTIVE.value:
        raise_player_error(
            PlayerErrorCodes.AUCTION_NOT_ACTIVE,
            "挂单非活跃状态",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    if listing.seller_id == player_uuid:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "不能给自己的挂单出价",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    min_bid = listing.current_price + 1
    if body.bid_amount < min_bid:
        raise_player_error(
            PlayerErrorCodes.BID_TOO_LOW,
            f"出价必须高于当前价格 {listing.current_price}",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    wallet = await wallet_repo.get_wallet(player_uuid)
    if wallet is None or wallet.gold_coins < body.bid_amount:
        raise_player_error(
            PlayerErrorCodes.INSUFFICIENT_GOLD,
            "金币不足",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    updated_listing = await auction_repo.place_bid(listing_id, player_uuid, body.bid_amount)

    return EnvelopeResponse(
        request_id=request_id,
        data=AuctionResponse.model_validate(updated_listing),
        trace_id=trace_id,
    )


@router.post(
    "/player/auction/listings/{listing_id}/buyout",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Listing not found"},
        409: {"description": "No buyout price or insufficient gold"},
    },
    tags=["auction"],
)
async def buyout_auction(
    listing_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[AuctionResponse]:
    """一口价购买"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_auction_buyout")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    auction_repo = AuctionRepository(db)
    wallet_repo = WalletRepository(db)

    listing = await auction_repo.get_listing_by_id(listing_id)
    if listing is None:
        raise_player_error(
            PlayerErrorCodes.AUCTION_NOT_FOUND,
            "挂单不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if listing.status != AuctionStatus.ACTIVE.value:
        raise_player_error(
            PlayerErrorCodes.AUCTION_NOT_ACTIVE,
            "挂单非活跃状态",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    if listing.seller_id == player_uuid:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "不能购买自己的挂单",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if listing.buyout_price is None:
        raise_player_error(
            PlayerErrorCodes.AUCTION_NO_BUYOUT,
            "该挂单没有一口价",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    wallet = await wallet_repo.get_wallet(player_uuid)
    if wallet is None or wallet.gold_coins < listing.buyout_price:
        raise_player_error(
            PlayerErrorCodes.INSUFFICIENT_GOLD,
            "金币不足",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    updated_listing = await auction_repo.buyout(listing_id, player_uuid)

    return EnvelopeResponse(
        request_id=request_id,
        data=AuctionResponse.model_validate(updated_listing),
        trace_id=trace_id,
    )


@router.get(
    "/player/auction/listings",
    responses={
        401: {"description": "Unauthorized"},
    },
    tags=["auction"],
)
async def get_auction_listings(
    request: Request,
    item_key: str | None = Query(default=None),
    item_type: str | None = Query(default=None),
    listing_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[AuctionListResponse]:
    """获取拍卖行挂单列表"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_auction_list")

    try:
        uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    auction_repo = AuctionRepository(db)
    listings, total = await auction_repo.get_active_listings(
        item_key=item_key, item_type=item_type, limit=limit, offset=offset
    )

    listing_responses = [AuctionResponse.model_validate(listing) for listing in listings]

    return EnvelopeResponse(
        request_id=request_id,
        data=AuctionListResponse(listings=listing_responses, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/player/auction/listings/{listing_id}",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Listing not found"},
    },
    tags=["auction"],
)
async def get_auction_listing(
    listing_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[AuctionResponse]:
    """获取挂单详情"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_auction_detail")

    try:
        uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    auction_repo = AuctionRepository(db)
    listing = await auction_repo.get_listing_by_id(listing_id)

    if listing is None:
        raise_player_error(
            PlayerErrorCodes.AUCTION_NOT_FOUND,
            "挂单不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=AuctionResponse.model_validate(listing),
        trace_id=trace_id,
    )


@router.get(
    "/player/auction/my-listings",
    responses={
        401: {"description": "Unauthorized"},
    },
    tags=["auction"],
)
async def get_my_auction_listings(
    request: Request,
    listing_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[AuctionListResponse]:
    """获取我的挂单列表"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_auction_my")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    auction_repo = AuctionRepository(db)
    listings, total = await auction_repo.get_seller_listings(player_uuid, status=listing_status, limit=limit, offset=offset)

    listing_responses = [AuctionResponse.model_validate(listing) for listing in listings]

    return EnvelopeResponse(
        request_id=request_id,
        data=AuctionListResponse(listings=listing_responses, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


# === 钱包 API ===


@router.get(
    "/player/wallet",
    responses={
        401: {"description": "Unauthorized"},
    },
    tags=["wallet"],
)
async def get_player_wallet(
    request: Request,
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[WalletResponse]:
    """获取玩家钱包"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_wallet_get")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    wallet_repo = WalletRepository(db)
    wallet = await wallet_repo.get_wallet(player_uuid)

    if wallet is None:
        raise_player_error(
            PlayerErrorCodes.WALLET_NOT_FOUND,
            "钱包不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=WalletResponse.model_validate(wallet),
        trace_id=trace_id,
    )


@router.get(
    "/player/wallet/transactions",
    responses={
        401: {"description": "Unauthorized"},
    },
    tags=["wallet"],
)
async def get_wallet_transactions(
    request: Request,
    transaction_type: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequirePlayerRole,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[WalletTransactionListResponse]:
    """获取钱包交易记录"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_wallet_transactions")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    wallet_repo = WalletRepository(db)
    transactions, total = await wallet_repo.get_transactions(
        player_uuid, transaction_type=transaction_type, limit=limit, offset=offset
    )

    transaction_responses = [WalletTransactionResponse.model_validate(t) for t in transactions]

    return EnvelopeResponse(
        request_id=request_id,
        data=WalletTransactionListResponse(transactions=transaction_responses, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


# ============================================================
# 公会战相关 API
# ============================================================


@router.post(
    "/player/guild/wars",
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not guild leader/officer"},
        409: {"description": "Cannot declare war"},
    },
    tags=["guild-wars"],
)
async def declare_war(
    request: Request,
    body: DeclareWarRequest,
    current_user: UserPayload = RequireGuildWarWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildWarResponse]:
    """宣战（公会会长/官员）"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_war_declare")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    war_repo = GuildWarRepository(db)
    audit_repo = AuditRepository(db)

    # 获取玩家所在公会
    guild = await guild_repo.get_guild_by_player(player_uuid)
    if guild is None:
        raise_player_error(
            PlayerErrorCodes.NOT_IN_GUILD,
            "您未加入任何公会",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # 检查是否为会长或官员
    if not await guild_repo.is_guild_officer(guild.guild_id, player_uuid):
        raise_player_error(
            PlayerErrorCodes.NOT_GUILD_LEADER_OR_OFFICER,
            "只有会长或官员才能宣战",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # 检查不能对自身公会宣战
    if guild.guild_id == body.defender_guild_id:
        raise_player_error(
            PlayerErrorCodes.CANNOT_DECLARE_WAR_ON_SELF,
            "不能对自身公会宣战",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 检查防守方公会是否存在
    defender_guild = await guild_repo.get_guild_by_id(body.defender_guild_id)
    if defender_guild is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_NOT_FOUND,
            "目标公会不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # 检查是否已有进行中的战争
    if await war_repo.has_active_war_between(guild.guild_id, body.defender_guild_id):
        raise_player_error(
            PlayerErrorCodes.GUILD_WAR_ALREADY_EXISTS,
            "两个公会之间已有进行中的战争",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    war = await war_repo.declare_war(
        challenger_guild_id=guild.guild_id,
        defender_guild_id=body.defender_guild_id,
        war_type=body.war_type.value,
        reward_config=body.reward_config,
    )

    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role="player",
        action=ACTION_GUILD_WAR_DECLARE,
        resource_type=RESOURCE_GUILD_WAR,
        resource_id=war.war_id,
        request_payload_jsonb={"defender_guild_id": str(body.defender_guild_id), "war_type": body.war_type.value},
        result_status=201,
    )

    record_guild_war_declared(str(guild.guild_id))

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildWarResponse.model_validate(war),
        trace_id=trace_id,
    )


@router.post(
    "/player/guild/wars/{war_id}/accept",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not defender guild leader"},
        409: {"description": "War not in declared status"},
    },
    tags=["guild-wars"],
)
async def accept_war(
    request: Request,
    war_id: uuid.UUID,
    current_user: UserPayload = RequireGuildWarWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildWarResponse]:
    """接受宣战（防守方公会会长）"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_war_accept")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    war_repo = GuildWarRepository(db)
    audit_repo = AuditRepository(db)

    war = await war_repo.get_war(war_id)
    if war is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_WAR_NOT_FOUND,
            "公会战不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if war.status != "declared":
        raise_player_error(
            PlayerErrorCodes.GUILD_WAR_NOT_DECLARED,
            "公会战不在宣战状态",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    # 获取玩家所在公会
    guild = await guild_repo.get_guild_by_player(player_uuid)
    if guild is None or guild.guild_id != war.defender_guild_id:
        raise_player_error(
            PlayerErrorCodes.NOT_GUILD_LEADER_OR_OFFICER,
            "只有防守方公会会长才能接受宣战",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    if not await guild_repo.is_guild_officer(guild.guild_id, player_uuid):
        raise_player_error(
            PlayerErrorCodes.NOT_GUILD_LEADER_OR_OFFICER,
            "只有会长或官员才能接受宣战",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    war = await war_repo.accept_war(war_id)

    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role="player",
        action=ACTION_GUILD_WAR_ACCEPT,
        resource_type=RESOURCE_GUILD_WAR,
        resource_id=war_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildWarResponse.model_validate(war),
        trace_id=trace_id,
    )


@router.post(
    "/player/guild/wars/{war_id}/cancel",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not challenger guild leader"},
        409: {"description": "War not in declared status"},
    },
    tags=["guild-wars"],
)
async def cancel_war(
    request: Request,
    war_id: uuid.UUID,
    current_user: UserPayload = RequireGuildWarWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildWarResponse]:
    """取消公会战（宣战方公会会长）"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_war_cancel")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    war_repo = GuildWarRepository(db)
    audit_repo = AuditRepository(db)

    war = await war_repo.get_war(war_id)
    if war is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_WAR_NOT_FOUND,
            "公会战不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if war.status != "declared":
        raise_player_error(
            PlayerErrorCodes.GUILD_WAR_NOT_DECLARED,
            "只有宣战状态的战争才能取消",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    guild = await guild_repo.get_guild_by_player(player_uuid)
    if guild is None or guild.guild_id != war.challenger_guild_id:
        raise_player_error(
            PlayerErrorCodes.NOT_GUILD_LEADER_OR_OFFICER,
            "只有宣战方公会会长才能取消战争",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    if not await guild_repo.is_guild_officer(guild.guild_id, player_uuid):
        raise_player_error(
            PlayerErrorCodes.NOT_GUILD_LEADER_OR_OFFICER,
            "只有会长或官员才能取消战争",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    war = await war_repo.cancel_war(war_id, guild.guild_id)

    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role="player",
        action=ACTION_GUILD_WAR_CANCEL,
        resource_type=RESOURCE_GUILD_WAR,
        resource_id=war_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildWarResponse.model_validate(war),
        trace_id=trace_id,
    )


@router.get(
    "/player/guild/wars/active",
    responses={
        401: {"description": "Unauthorized"},
    },
    tags=["guild-wars"],
)
async def get_active_wars(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireGuildWarReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildWarListResponse]:
    """获取我方公会的进行中战争"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_war_active")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    war_repo = GuildWarRepository(db)

    guild = await guild_repo.get_guild_by_player(player_uuid)
    if guild is None:
        return EnvelopeResponse(
            request_id=request_id,
            data=GuildWarListResponse(wars=[], total=0),
            meta=PaginatedMeta(total=0, limit=limit, offset=offset),
            trace_id=trace_id,
        )

    wars, total = await war_repo.get_active_wars(guild.guild_id, limit=limit, offset=offset)
    war_responses = [GuildWarResponse.model_validate(w) for w in wars]

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildWarListResponse(wars=war_responses, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/player/guild/wars/history",
    responses={
        401: {"description": "Unauthorized"},
    },
    tags=["guild-wars"],
)
async def get_war_history(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireGuildWarReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildWarListResponse]:
    """获取我方公会的战争历史"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_war_history")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    war_repo = GuildWarRepository(db)

    guild = await guild_repo.get_guild_by_player(player_uuid)
    if guild is None:
        return EnvelopeResponse(
            request_id=request_id,
            data=GuildWarListResponse(wars=[], total=0),
            meta=PaginatedMeta(total=0, limit=limit, offset=offset),
            trace_id=trace_id,
        )

    wars, total = await war_repo.get_guild_war_history(guild.guild_id, limit=limit, offset=offset)
    war_responses = [GuildWarResponse.model_validate(w) for w in wars]

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildWarListResponse(wars=war_responses, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/player/guild/wars/{war_id}",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "War not found"},
    },
    tags=["guild-wars"],
)
async def get_war_details(
    request: Request,
    war_id: uuid.UUID,
    current_user: UserPayload = RequireGuildWarReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildWarResponse]:
    """获取公会战详情"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_war_detail")

    war_repo = GuildWarRepository(db)

    war = await war_repo.get_war(war_id)
    if war is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_WAR_NOT_FOUND,
            "公会战不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildWarResponse.model_validate(war),
        trace_id=trace_id,
    )


@router.post(
    "/player/guild/wars/{war_id}/join",
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Unauthorized"},
        409: {"description": "Already joined or wrong guild"},
    },
    tags=["guild-wars"],
)
async def join_war(
    request: Request,
    war_id: uuid.UUID,
    body: JoinWarRequest,
    current_user: UserPayload = RequireGuildWarWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildWarParticipantResponse]:
    """加入公会战"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_war_join")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    war_repo = GuildWarRepository(db)
    audit_repo = AuditRepository(db)

    war = await war_repo.get_war(war_id)
    if war is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_WAR_NOT_FOUND,
            "公会战不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if war.status not in ("declared", "accepted", "in_progress"):
        raise_player_error(
            PlayerErrorCodes.GUILD_WAR_NOT_ACTIVE,
            "公会战不在可加入状态",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    # 检查玩家是否已加入
    if await war_repo.is_player_in_war(war_id, player_uuid):
        raise_player_error(
            PlayerErrorCodes.PLAYER_ALREADY_IN_WAR,
            "您已加入此公会战",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    # 检查玩家公会是否为参战方
    if body.guild_id != war.challenger_guild_id and body.guild_id != war.defender_guild_id:
        raise_player_error(
            PlayerErrorCodes.CANNOT_JOIN_OPPONENT_AS_WRONG_GUILD,
            "您的公会不是参战方",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    participant = await war_repo.join_war(war_id, body.guild_id, player_uuid)

    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role="player",
        action=ACTION_GUILD_WAR_JOIN,
        resource_type=RESOURCE_GUILD_WAR_PARTICIPANT,
        resource_id=participant.participant_id,
        result_status=201,
    )

    record_guild_war_participant_joined(str(war_id))

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildWarParticipantResponse.model_validate(participant),
        trace_id=trace_id,
    )


@router.get(
    "/player/guild/wars/{war_id}/scoreboard",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "War not found"},
    },
    tags=["guild-wars"],
)
async def get_war_scoreboard(
    request: Request,
    war_id: uuid.UUID,
    current_user: UserPayload = RequireGuildWarReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[WarScoreboardResponse]:
    """获取公会战记分板"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_war_scoreboard")

    war_repo = GuildWarRepository(db)

    war = await war_repo.get_war(war_id)
    if war is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_WAR_NOT_FOUND,
            "公会战不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    challenger_participants, defender_participants = await war_repo.get_war_scoreboard(war_id)

    return EnvelopeResponse(
        request_id=request_id,
        data=WarScoreboardResponse(
            challenger_participants=[
                GuildWarParticipantResponse.model_validate(p) for p in challenger_participants
            ],
            defender_participants=[
                GuildWarParticipantResponse.model_validate(p) for p in defender_participants
            ],
        ),
        trace_id=trace_id,
    )


@router.post(
    "/player/guild/wars/{war_id}/complete",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not authorized"},
        404: {"description": "War not found"},
    },
    tags=["guild-wars"],
)
async def complete_war(
    request: Request,
    war_id: uuid.UUID,
    winner_guild_id: uuid.UUID = Query(...),
    current_user: UserPayload = RequireGuildWarWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[GuildWarResponse]:
    """完成公会战"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_war_complete")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    guild_repo = GuildRepository(db)
    war_repo = GuildWarRepository(db)
    audit_repo = AuditRepository(db)

    war = await war_repo.get_war(war_id)
    if war is None:
        raise_player_error(
            PlayerErrorCodes.GUILD_WAR_NOT_FOUND,
            "公会战不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if war.status != "in_progress":
        raise_player_error(
            PlayerErrorCodes.GUILD_WAR_NOT_ACTIVE,
            "公会战不在进行中状态",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    guild = await guild_repo.get_guild_by_player(player_uuid)
    if guild is None:
        raise_player_error(
            PlayerErrorCodes.NOT_IN_GUILD,
            "您未加入任何公会",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    if not await guild_repo.is_guild_officer(guild.guild_id, player_uuid):
        raise_player_error(
            PlayerErrorCodes.NOT_GUILD_LEADER_OR_OFFICER,
            "只有会长或官员才能结束战争",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    war = await war_repo.complete_war(war_id, winner_guild_id)

    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role="player",
        action=ACTION_GUILD_WAR_COMPLETE,
        resource_type=RESOURCE_GUILD_WAR,
        resource_id=war_id,
        request_payload_jsonb={"winner_guild_id": str(winner_guild_id)},
        result_status=200,
    )

    record_guild_war_completed(str(winner_guild_id))

    return EnvelopeResponse(
        request_id=request_id,
        data=GuildWarResponse.model_validate(war),
        trace_id=trace_id,
    )


# ============================================================
# 好友协作任务相关 API
# ============================================================


@router.post(
    "/player/friend/collab-quests",
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Unauthorized"},
        409: {"description": "Cannot create collab quest"},
    },
    tags=["collab-quests"],
)
async def create_collab_quest(
    request: Request,
    body: CreateFriendCollabQuestRequest,
    current_user: UserPayload = RequireCollabQuestWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[FriendCollabQuestResponse]:
    """创建好友协作任务"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_collab_create")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 检查不能与自己协作
    if player_uuid == body.friend_id:
        raise_player_error(
            PlayerErrorCodes.CANNOT_COLLAB_WITH_SELF,
            "不能与自己创建协作任务",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 检查是否为好友
    friend_repo = FriendRepository(db)
    friend_member = await friend_repo.get_friendship(player_uuid, body.friend_id)
    if friend_member is None or friend_member.status != "accepted":
        raise_player_error(
            PlayerErrorCodes.NOT_FRIENDS_FOR_COLLAB,
            "只能与好友创建协作任务",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    quest_repo = FriendCollabQuestRepository(db)
    audit_repo = AuditRepository(db)

    quest = await quest_repo.create_quest(
        initiator_id=player_uuid,
        friend_id=body.friend_id,
        quest_type=body.quest_type.value,
        title=body.title,
        objectives=body.objectives,
        rewards=body.rewards,
        expires_at=body.expires_at,
        description=body.description if hasattr(body, "description") else None,
    )

    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role="player",
        action=ACTION_COLLAB_QUEST_CREATE,
        resource_type=RESOURCE_COLLAB_QUEST,
        resource_id=quest.quest_id,
        request_payload_jsonb={"friend_id": str(body.friend_id), "quest_type": body.quest_type.value},
        result_status=201,
    )

    record_collab_quest_created(current_user.user_id)

    return EnvelopeResponse(
        request_id=request_id,
        data=FriendCollabQuestResponse.model_validate(quest),
        trace_id=trace_id,
    )


@router.post(
    "/player/friend/collab-quests/{quest_id}/accept",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not the invited friend"},
        409: {"description": "Quest not pending"},
    },
    tags=["collab-quests"],
)
async def accept_collab_quest(
    request: Request,
    quest_id: uuid.UUID,
    current_user: UserPayload = RequireCollabQuestWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[FriendCollabQuestResponse]:
    """接受协作任务邀请"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_collab_accept")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    quest_repo = FriendCollabQuestRepository(db)
    audit_repo = AuditRepository(db)

    quest = await quest_repo.get_quest(quest_id)
    if quest is None:
        raise_player_error(
            PlayerErrorCodes.COLLAB_QUEST_NOT_FOUND,
            "协作任务不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if quest.friend_id != player_uuid:
        raise_player_error(
            PlayerErrorCodes.COLLAB_QUEST_INVITE_NOT_FOR_YOU,
            "此协作任务邀请不是发给您的",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    if quest.status != "pending_invite":
        raise_player_error(
            PlayerErrorCodes.COLLAB_QUEST_NOT_PENDING,
            "协作任务不在待接受状态",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    quest = await quest_repo.accept_quest(quest_id)

    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role="player",
        action=ACTION_COLLAB_QUEST_ACCEPT,
        resource_type=RESOURCE_COLLAB_QUEST,
        resource_id=quest_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=FriendCollabQuestResponse.model_validate(quest),
        trace_id=trace_id,
    )


@router.post(
    "/player/friend/collab-quests/{quest_id}/reject",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Not the invited friend"},
        409: {"description": "Quest not pending"},
    },
    tags=["collab-quests"],
)
async def reject_collab_quest(
    request: Request,
    quest_id: uuid.UUID,
    current_user: UserPayload = RequireCollabQuestWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[FriendCollabQuestResponse]:
    """拒绝协作任务邀请"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_collab_reject")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    quest_repo = FriendCollabQuestRepository(db)
    audit_repo = AuditRepository(db)

    quest = await quest_repo.get_quest(quest_id)
    if quest is None:
        raise_player_error(
            PlayerErrorCodes.COLLAB_QUEST_NOT_FOUND,
            "协作任务不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if quest.friend_id != player_uuid:
        raise_player_error(
            PlayerErrorCodes.COLLAB_QUEST_INVITE_NOT_FOR_YOU,
            "此协作任务邀请不是发给您的",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    if quest.status != "pending_invite":
        raise_player_error(
            PlayerErrorCodes.COLLAB_QUEST_NOT_PENDING,
            "协作任务不在待接受状态",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    quest = await quest_repo.reject_quest(quest_id)

    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role="player",
        action=ACTION_COLLAB_QUEST_REJECT,
        resource_type=RESOURCE_COLLAB_QUEST,
        resource_id=quest_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=FriendCollabQuestResponse.model_validate(quest),
        trace_id=trace_id,
    )


@router.post(
    "/player/friend/collab-quests/{quest_id}/progress",
    responses={
        401: {"description": "Unauthorized"},
        409: {"description": "Quest not active"},
    },
    tags=["collab-quests"],
)
async def update_collab_quest_progress(
    request: Request,
    quest_id: uuid.UUID,
    body: UpdateFriendCollabQuestProgressRequest,
    current_user: UserPayload = RequireCollabQuestWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[FriendCollabQuestResponse]:
    """更新协作任务进度"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_collab_progress")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    quest_repo = FriendCollabQuestRepository(db)
    audit_repo = AuditRepository(db)

    quest = await quest_repo.get_quest(quest_id)
    if quest is None:
        raise_player_error(
            PlayerErrorCodes.COLLAB_QUEST_NOT_FOUND,
            "协作任务不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if quest.status != "active":
        raise_player_error(
            PlayerErrorCodes.COLLAB_QUEST_NOT_ACTIVE,
            "协作任务不在进行中状态",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    quest = await quest_repo.update_progress(quest_id, player_uuid, body.progress_data)

    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role="player",
        action=ACTION_COLLAB_QUEST_PROGRESS,
        resource_type=RESOURCE_COLLAB_QUEST,
        resource_id=quest_id,
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=FriendCollabQuestResponse.model_validate(quest),
        trace_id=trace_id,
    )


@router.post(
    "/player/friend/collab-quests/{quest_id}/complete",
    responses={
        401: {"description": "Unauthorized"},
        409: {"description": "Quest not active"},
    },
    tags=["collab-quests"],
)
async def complete_collab_quest(
    request: Request,
    quest_id: uuid.UUID,
    current_user: UserPayload = RequireCollabQuestWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[FriendCollabQuestResponse]:
    """完成协作任务"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_collab_complete")

    try:
        uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    quest_repo = FriendCollabQuestRepository(db)
    audit_repo = AuditRepository(db)

    quest = await quest_repo.get_quest(quest_id)
    if quest is None:
        raise_player_error(
            PlayerErrorCodes.COLLAB_QUEST_NOT_FOUND,
            "协作任务不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if quest.status != "active":
        raise_player_error(
            PlayerErrorCodes.COLLAB_QUEST_NOT_ACTIVE,
            "协作任务不在进行中状态",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    quest = await quest_repo.complete_quest(quest_id)

    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role="player",
        action=ACTION_COLLAB_QUEST_COMPLETE,
        resource_type=RESOURCE_COLLAB_QUEST,
        resource_id=quest_id,
        result_status=200,
    )

    record_collab_quest_completed(current_user.user_id)

    return EnvelopeResponse(
        request_id=request_id,
        data=FriendCollabQuestResponse.model_validate(quest),
        trace_id=trace_id,
    )


@router.get(
    "/player/friend/collab-quests/active",
    responses={
        401: {"description": "Unauthorized"},
    },
    tags=["collab-quests"],
)
async def get_active_collab_quests(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireCollabQuestReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[FriendCollabQuestListResponse]:
    """获取进行中的协作任务"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_collab_active")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    quest_repo = FriendCollabQuestRepository(db)
    quests, total = await quest_repo.get_active_quests(player_uuid, limit=limit, offset=offset)
    quest_responses = [FriendCollabQuestResponse.model_validate(q) for q in quests]

    return EnvelopeResponse(
        request_id=request_id,
        data=FriendCollabQuestListResponse(quests=quest_responses, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/player/friend/collab-quests/pending",
    responses={
        401: {"description": "Unauthorized"},
    },
    tags=["collab-quests"],
)
async def get_pending_collab_quests(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireCollabQuestReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[FriendCollabQuestListResponse]:
    """获取待处理的协作任务邀请"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_collab_pending")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    quest_repo = FriendCollabQuestRepository(db)
    quests, total = await quest_repo.get_pending_invites(player_uuid, limit=limit, offset=offset)
    quest_responses = [FriendCollabQuestResponse.model_validate(q) for q in quests]

    return EnvelopeResponse(
        request_id=request_id,
        data=FriendCollabQuestListResponse(quests=quest_responses, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/player/friend/collab-quests/history",
    responses={
        401: {"description": "Unauthorized"},
    },
    tags=["collab-quests"],
)
async def get_collab_quest_history(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireCollabQuestReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[FriendCollabQuestListResponse]:
    """获取协作任务历史"""
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_collab_history")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    quest_repo = FriendCollabQuestRepository(db)
    quests, total = await quest_repo.get_quest_history(player_uuid, limit=limit, offset=offset)
    quest_responses = [FriendCollabQuestResponse.model_validate(q) for q in quests]

    return EnvelopeResponse(
        request_id=request_id,
        data=FriendCollabQuestListResponse(quests=quest_responses, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@ops_router.get("/economy/overview", tags=["economy"])
async def get_economy_overview(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireEconomyReadScope,
) -> EnvelopeResponse[EconomicOverview]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_econ_overview")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_ECONOMY_OVERVIEW_QUERY,
        resource_type=RESOURCE_ECONOMY,
        resource_id=None,
        trace_id=trace_id,
    )

    try:
        econ_repo = EconomicRepository(db)
        overview_data = await econ_repo.get_economy_overview()
        overview = EconomicOverview(**overview_data)
    except Exception:
        raise_player_error(
            PlayerErrorCodes.ECONOMY_STATS_QUERY_FAILED,
            "经济统计查询失败",
            request_id,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=overview,
        trace_id=trace_id,
    )


@ops_router.get("/economy/trades", tags=["economy"])
async def get_trade_stats(
    request: Request,
    days: int = Query(7, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireEconomyReadScope,
) -> EnvelopeResponse[dict]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_econ_trades")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_ECONOMY_TRADE_STATS_QUERY,
        resource_type=RESOURCE_ECONOMY,
        resource_id=None,
        trace_id=trace_id,
    )

    try:
        econ_repo = EconomicRepository(db)
        stats, total = await econ_repo.get_trade_stats(days=days, limit=limit, offset=offset)
        items = [TradeStatsItem(**item) for item in stats]
    except Exception:
        raise_player_error(
            PlayerErrorCodes.ECONOMY_STATS_QUERY_FAILED,
            "交易统计查询失败",
            request_id,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data={"items": items, "total": total},
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@ops_router.get("/economy/auctions", tags=["economy"])
async def get_auction_stats(
    request: Request,
    days: int = Query(7, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireEconomyReadScope,
) -> EnvelopeResponse[dict]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_econ_auctions")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_ECONOMY_AUCTION_STATS_QUERY,
        resource_type=RESOURCE_ECONOMY,
        resource_id=None,
        trace_id=trace_id,
    )

    try:
        econ_repo = EconomicRepository(db)
        stats, total = await econ_repo.get_auction_stats(days=days, limit=limit, offset=offset)
        items = [AuctionStatsItem(**item) for item in stats]
    except Exception:
        raise_player_error(
            PlayerErrorCodes.ECONOMY_STATS_QUERY_FAILED,
            "拍卖统计查询失败",
            request_id,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data={"items": items, "total": total},
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@ops_router.get("/economy/wallets", tags=["economy"])
async def get_wallet_stats(
    request: Request,
    days: int = Query(7, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireEconomyReadScope,
) -> EnvelopeResponse[dict]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_econ_wallets")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_ECONOMY_WALLET_STATS_QUERY,
        resource_type=RESOURCE_ECONOMY,
        resource_id=None,
        trace_id=trace_id,
    )

    try:
        econ_repo = EconomicRepository(db)
        stats, total = await econ_repo.get_wallet_stats(days=days, limit=limit, offset=offset)
        items = [WalletStatsItem(**item) for item in stats]
    except Exception:
        raise_player_error(
            PlayerErrorCodes.ECONOMY_STATS_QUERY_FAILED,
            "钱包统计查询失败",
            request_id,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data={"items": items, "total": total},
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@ops_router.get("/economy/trends", tags=["economy"])
async def get_economic_trends(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    granularity: str = Query("day"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireEconomyReadScope,
) -> EnvelopeResponse[dict]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_econ_trends")

    if granularity not in ("day", "week"):
        raise_player_error(
            PlayerErrorCodes.INVALID_TREND_GRANULARITY,
            "无效的趋势粒度，仅支持 day 或 week",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_ECONOMY_TRENDS_QUERY,
        resource_type=RESOURCE_ECONOMY,
        resource_id=None,
        trace_id=trace_id,
    )

    try:
        econ_repo = EconomicRepository(db)
        trends = await econ_repo.get_economic_trends(days=days, granularity=granularity)
        items = [EconomicTrendPoint(**item) for item in trends]
    except Exception:
        raise_player_error(
            PlayerErrorCodes.ECONOMY_STATS_QUERY_FAILED,
            "经济趋势查询失败",
            request_id,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data={"items": items, "total": len(items)},
        trace_id=trace_id,
    )


@ops_router.get("/economy/top-traders", tags=["economy"])
async def get_top_traders(
    request: Request,
    days: int = Query(7, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireEconomyReadScope,
) -> EnvelopeResponse[dict]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_econ_top_traders")

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_ECONOMY_TOP_TRADERS_QUERY,
        resource_type=RESOURCE_ECONOMY,
        resource_id=None,
        trace_id=trace_id,
    )

    try:
        econ_repo = EconomicRepository(db)
        traders, total = await econ_repo.get_top_traders(days=days, limit=limit, offset=offset)
        items = [TopTraderItem(**item) for item in traders]
    except Exception:
        raise_player_error(
            PlayerErrorCodes.ECONOMY_STATS_QUERY_FAILED,
            "交易排行查询失败",
            request_id,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data={"items": items, "total": total},
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


# === 匹配系统 API ===


@router.get(
    "/player/match/rating",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "No active season"},
    },
    tags=["match"],
)
async def get_my_rating(
    request: Request,
    current_user: UserPayload = RequireMatchReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[PlayerRatingResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_match_rating")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    season_repo = MatchSeasonRepository(db)
    current_season = await season_repo.get_current_season()
    if current_season is None:
        raise_player_error(
            PlayerErrorCodes.NO_ACTIVE_SEASON,
            "当前没有活跃的赛季",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    rating_repo = PlayerRatingRepository(db)
    rating = await rating_repo.get_or_create_rating(player_uuid, current_season.season_id)

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_MATCH_RATING_QUERY,
        resource_type=RESOURCE_PLAYER_RATING,
        resource_id=rating.rating_id,
        request_payload_jsonb={"season_id": str(current_season.season_id)},
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=PlayerRatingResponse.model_validate(rating),
        trace_id=trace_id,
    )


@router.post(
    "/player/match/queue/join",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "No active season"},
        409: {"description": "Already in queue"},
    },
    tags=["match"],
)
async def join_match_queue(
    body: JoinMatchQueueRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: UserPayload = RequireMatchWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[MatchQueueResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_match_queue_join")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    season_repo = MatchSeasonRepository(db)
    current_season = await season_repo.get_current_season()
    if current_season is None:
        raise_player_error(
            PlayerErrorCodes.NO_ACTIVE_SEASON,
            "当前没有活跃的赛季",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    queue_repo = MatchQueueRepository(db)
    in_queue = await queue_repo.is_player_in_queue(player_uuid, current_season.season_id)
    if in_queue:
        raise_player_error(
            PlayerErrorCodes.PLAYER_ALREADY_IN_QUEUE,
            "玩家已在匹配队列中",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    rating_repo = PlayerRatingRepository(db)
    rating = await rating_repo.get_or_create_rating(player_uuid, current_season.season_id)

    player_repo = PlayerRepository(db)
    player = await player_repo.get_player_by_id(player_uuid)
    player_level = player.level if player else 1

    queue_item = await queue_repo.join_queue(
        player_id=player_uuid,
        season_id=current_season.season_id,
        match_mode=body.match_mode.value,
        tier=rating.tier,
        division=rating.division,
        player_level=player_level,
    )

    record_match_queue_joined(str(player_uuid), body.match_mode.value)

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_MATCH_QUEUE_JOIN,
        resource_type=RESOURCE_MATCH_QUEUE,
        resource_id=queue_item.queue_id,
        request_payload_jsonb={
            "season_id": str(current_season.season_id),
            "match_mode": body.match_mode.value,
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=MatchQueueResponse.model_validate(queue_item),
        trace_id=trace_id,
    )


@router.post(
    "/player/match/queue/leave",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Not in queue"},
    },
    tags=["match"],
)
async def leave_match_queue(
    body: LeaveMatchQueueRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: UserPayload = RequireMatchWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[MatchQueueResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_match_queue_leave")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    season_repo = MatchSeasonRepository(db)
    current_season = await season_repo.get_current_season()
    if current_season is None:
        raise_player_error(
            PlayerErrorCodes.NO_ACTIVE_SEASON,
            "当前没有活跃的赛季",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    queue_repo = MatchQueueRepository(db)
    queue_item = await queue_repo.leave_queue(player_uuid, current_season.season_id)
    if queue_item is None:
        raise_player_error(
            PlayerErrorCodes.PLAYER_NOT_IN_QUEUE,
            "玩家不在匹配队列中",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    record_match_queue_left(str(player_uuid), queue_item.match_mode)

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_MATCH_QUEUE_LEAVE,
        resource_type=RESOURCE_MATCH_QUEUE,
        resource_id=queue_item.queue_id,
        request_payload_jsonb={
            "season_id": str(current_season.season_id),
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=MatchQueueResponse.model_validate(queue_item),
        trace_id=trace_id,
    )


@router.get(
    "/player/match/queue/status",
    responses={
        401: {"description": "Unauthorized"},
    },
    tags=["match"],
)
async def get_match_queue_status(
    request: Request,
    current_user: UserPayload = RequireMatchReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[MatchQueueResponse | None]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_match_queue_status")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    season_repo = MatchSeasonRepository(db)
    current_season = await season_repo.get_current_season()
    if current_season is None:
        raise_player_error(
            PlayerErrorCodes.NO_ACTIVE_SEASON,
            "当前没有活跃的赛季",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    queue_repo = MatchQueueRepository(db)
    queue_item = await queue_repo.get_player_queue_status(player_uuid, current_season.season_id)

    data = MatchQueueResponse.model_validate(queue_item) if queue_item else None

    return EnvelopeResponse(
        request_id=request_id,
        data=data,
        trace_id=trace_id,
    )


@router.get(
    "/player/match/rooms/{room_id}",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Room not found"},
    },
    tags=["match"],
)
async def get_match_room(
    room_id: uuid.UUID,
    request: Request,
    current_user: UserPayload = RequireMatchReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[MatchRoomResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_match_room")

    room_repo = MatchRoomRepository(db)
    room = await room_repo.get_room(room_id)
    if room is None:
        raise_player_error(
            PlayerErrorCodes.MATCH_ROOM_NOT_FOUND,
            "对战房间不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return EnvelopeResponse(
        request_id=request_id,
        data=MatchRoomResponse.model_validate(room),
        trace_id=trace_id,
    )


@router.post(
    "/player/match/rooms/{room_id}/ready",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Room not found"},
        409: {"description": "Invalid room status"},
    },
    tags=["match"],
)
async def match_room_ready(
    room_id: uuid.UUID,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: UserPayload = RequireMatchWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[MatchRoomResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_match_room_ready")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    room_repo = MatchRoomRepository(db)
    room = await room_repo.get_room(room_id)
    if room is None:
        raise_player_error(
            PlayerErrorCodes.MATCH_ROOM_NOT_FOUND,
            "对战房间不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if room.status not in ("waiting", "ready"):
        raise_player_error(
            PlayerErrorCodes.MATCH_ROOM_INVALID_STATUS,
            f"当前房间状态 {room.status} 不允许准备",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    if room.player1_id != player_uuid and room.player2_id != player_uuid:
        raise_player_error(
            PlayerErrorCodes.PLAYER_NOT_IN_ROOM,
            "玩家不在该对战房间中",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    room = await room_repo.player_ready(room_id, player_uuid)
    assert room is not None

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_MATCH_ROOM_READY,
        resource_type=RESOURCE_MATCH_ROOM,
        resource_id=room.room_id,
        request_payload_jsonb={"room_id": str(room_id)},
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=MatchRoomResponse.model_validate(room),
        trace_id=trace_id,
    )


@router.post(
    "/player/match/rooms/{room_id}/result",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Room not found"},
        409: {"description": "Already completed or invalid status"},
    },
    tags=["match"],
)
async def submit_match_result(
    room_id: uuid.UUID,
    body: SubmitMatchResultRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: UserPayload = RequireMatchWriteScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[MatchResultResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_match_result_submit")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    room_repo = MatchRoomRepository(db)
    room = await room_repo.get_room(room_id)
    if room is None:
        raise_player_error(
            PlayerErrorCodes.MATCH_ROOM_NOT_FOUND,
            "对战房间不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if room.status == "completed":
        raise_player_error(
            PlayerErrorCodes.MATCH_ALREADY_COMPLETED,
            "对战已完成，无法重复提交结果",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    if room.player1_id != player_uuid and room.player2_id != player_uuid:
        raise_player_error(
            PlayerErrorCodes.PLAYER_NOT_IN_ROOM,
            "玩家不在该对战房间中",
            request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    room = await room_repo.submit_result(room_id, body.winner_id, body.match_data)
    assert room is not None

    winner_id = room.winner_id
    assert winner_id is not None
    loser_id = room.player2_id if winner_id == room.player1_id else room.player1_id

    rating_repo = PlayerRatingRepository(db)
    winner_rating = await rating_repo.get_player_rating(winner_id, room.season_id)
    loser_rating = await rating_repo.get_player_rating(loser_id, room.season_id)

    if winner_rating is None or loser_rating is None:
        winner_rating = await rating_repo.get_or_create_rating(winner_id, room.season_id)
        loser_rating = await rating_repo.get_or_create_rating(loser_id, room.season_id)

    winner_gain, loser_loss = calculate_rating_change(
        winner_rating.tier, winner_rating.division,
        loser_rating.tier, loser_rating.division,
    )

    winner_tier_before = winner_rating.tier
    winner_division_before = winner_rating.division
    loser_tier_before = loser_rating.tier
    loser_division_before = loser_rating.division

    await rating_repo.update_rating_after_match(
        winner_id, room.season_id, is_winner=True, rating_change=winner_gain
    )
    await rating_repo.update_rating_after_match(
        loser_id, room.season_id, is_winner=False, rating_change=loser_loss
    )

    winner_after = await rating_repo.get_player_rating(winner_id, room.season_id)
    loser_after = await rating_repo.get_player_rating(loser_id, room.season_id)

    result_repo = MatchResultRepository(db)
    result = await result_repo.create_result(
        room_id=room.room_id,
        season_id=room.season_id,
        match_mode=room.match_mode,
        winner_id=winner_id,
        loser_id=loser_id,
        is_draw=False,
        winner_rating_change=winner_gain,
        loser_rating_change=-loser_loss,
        winner_tier_before=winner_tier_before,
        winner_division_before=winner_division_before,
        winner_tier_after=winner_after.tier if winner_after else winner_tier_before,
        winner_division_after=winner_after.division if winner_after else winner_division_before,
        loser_tier_before=loser_tier_before,
        loser_division_before=loser_division_before,
        loser_tier_after=loser_after.tier if loser_after else loser_tier_before,
        loser_division_after=loser_after.division if loser_after else loser_division_before,
        submitted_by=player_uuid,
        match_data=body.match_data,
    )

    record_match_result_submitted(room.match_mode)
    record_match_rating_change(str(winner_id))
    record_match_rating_change(str(loser_id))

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_MATCH_RESULT_SUBMIT,
        resource_type=RESOURCE_MATCH_RESULT,
        resource_id=result.result_id,
        request_payload_jsonb={
            "room_id": str(room_id),
            "winner_id": str(body.winner_id),
        },
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=MatchResultResponse.model_validate(result),
        trace_id=trace_id,
    )


@router.get(
    "/player/match/history",
    responses={
        401: {"description": "Unauthorized"},
    },
    tags=["match"],
)
async def get_match_history(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireMatchReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[list[MatchResultResponse]]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_match_history")

    try:
        player_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        raise_player_error(
            PlayerErrorCodes.INVALID_PLAYER_ID,
            "无效的玩家ID格式",
            request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    result_repo = MatchResultRepository(db)
    results, total = await result_repo.get_player_match_history(
        player_uuid, limit=limit, offset=offset
    )

    result_responses = [MatchResultResponse.model_validate(r) for r in results]

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id or _make_request_id("trace"),
        request_id=request_id,
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_MATCH_HISTORY_QUERY,
        resource_type=RESOURCE_MATCH_RESULT,
        resource_id=player_uuid,
        request_payload_jsonb={"limit": limit, "offset": offset},
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=result_responses,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/player/match/leaderboard",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "No active season or season not found"},
    },
    tags=["match"],
)
async def get_match_leaderboard(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    season_id: uuid.UUID | None = Query(default=None, description="指定历史赛季ID，不传则查当前赛季"),
    current_user: UserPayload = RequireMatchReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[MatchLeaderboardResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_match_leaderboard")

    season_repo = MatchSeasonRepository(db)
    if season_id is not None:
        target_season = await season_repo.get_season(season_id)
        if target_season is None:
            raise_player_error(
                PlayerErrorCodes.MATCH_SEASON_NOT_FOUND,
                "指定的赛季不存在",
                request_id,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        target_season_id = target_season.season_id
    else:
        current_season = await season_repo.get_current_season()
        if current_season is None:
            raise_player_error(
                PlayerErrorCodes.NO_ACTIVE_SEASON,
                "当前没有活跃的赛季",
                request_id,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        target_season_id = current_season.season_id

    rating_repo = PlayerRatingRepository(db)
    ratings, total = await rating_repo.get_leaderboard(
        target_season_id, limit=limit, offset=offset
    )

    items: list[MatchLeaderboardItem] = []
    player_repo = PlayerRepository(db)
    for idx, rating in enumerate(ratings):
        player = await player_repo.get_player_by_id(rating.player_id)
        player_name = player.display_name if player else ""
        total_matches = rating.wins + rating.losses + rating.draws
        win_rate = rating.wins / total_matches if total_matches > 0 else 0.0
        items.append(
            MatchLeaderboardItem(
                player_id=rating.player_id,
                player_name=player_name,
                tier=MatchTier(rating.tier),
                division=rating.division,
                rating_points=rating.rating_points,
                wins=rating.wins,
                losses=rating.losses,
                win_rate=round(win_rate, 4),
                rank=offset + idx + 1,
            )
        )

    record_match_leaderboard_query(str(target_season_id))
    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=str(current_user.user_id),
        operator_role=current_user.role.value,
        action=ACTION_MATCH_LEADERBOARD_QUERY,
        resource_type=RESOURCE_PLAYER_RATING,
        resource_id=target_season_id,
        result_status=status.HTTP_200_OK,
    )
    await db.commit()

    return EnvelopeResponse(
        request_id=request_id,
        data=MatchLeaderboardResponse(items=items, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@router.get(
    "/player/match/leaderboard/me",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "No active season or player rating not found"},
    },
    tags=["match"],
)
async def get_my_rank(
    request: Request,
    season_id: uuid.UUID | None = Query(default=None, description="指定历史赛季ID"),
    current_user: UserPayload = RequireMatchReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[PlayerRankResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_match_rank")

    season_repo = MatchSeasonRepository(db)
    if season_id is not None:
        target_season = await season_repo.get_season(season_id)
        if target_season is None:
            raise_player_error(
                PlayerErrorCodes.MATCH_SEASON_NOT_FOUND,
                "指定的赛季不存在",
                request_id,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        target_season_id = target_season.season_id
    else:
        current_season = await season_repo.get_current_season()
        if current_season is None:
            raise_player_error(
                PlayerErrorCodes.NO_ACTIVE_SEASON,
                "当前没有活跃的赛季",
                request_id,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        target_season_id = current_season.season_id

    rating_repo = PlayerRatingRepository(db)
    player_uuid = uuid.UUID(current_user.user_id)
    rating = await rating_repo.get_player_rating(player_uuid, target_season_id)
    if rating is None:
        raise_player_error(
            PlayerErrorCodes.PLAYER_RATING_NOT_FOUND,
            "您在该赛季暂无段位记录",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    rank = await rating_repo.get_player_rank(player_uuid, target_season_id)
    if rank is None:
        rank = 0
    total_players = await rating_repo.count_active_players(target_season_id)

    player_repo = PlayerRepository(db)
    player = await player_repo.get_player_by_id(player_uuid)
    player_name = player.display_name if player else ""

    total_matches = rating.wins + rating.losses + rating.draws
    win_rate = rating.wins / total_matches if total_matches > 0 else 0.0

    record_match_player_rank_query(str(target_season_id))
    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=str(current_user.user_id),
        operator_role=current_user.role.value,
        action=ACTION_MATCH_RANK_QUERY,
        resource_type=RESOURCE_PLAYER_RATING,
        resource_id=rating.rating_id,
        result_status=status.HTTP_200_OK,
    )
    await db.commit()

    return EnvelopeResponse(
        request_id=request_id,
        data=PlayerRankResponse(
            player_id=current_user.user_id,
            player_name=player_name,
            season_id=target_season_id,
            rank=rank,
            tier=MatchTier(rating.tier),
            division=rating.division,
            rating_points=rating.rating_points,
            wins=rating.wins,
            losses=rating.losses,
            draws=rating.draws,
            win_streak=rating.win_streak,
            best_tier=MatchTier(rating.best_tier),
            best_division=rating.best_division,
            win_rate=round(win_rate, 4),
            total_matches=total_matches,
            total_players=total_players,
        ),
        trace_id=trace_id,
    )


@router.get(
    "/player/match/leaderboard/tier-distribution",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "No active season"},
    },
    tags=["match"],
)
async def get_tier_distribution(
    request: Request,
    season_id: uuid.UUID | None = Query(default=None, description="指定历史赛季ID"),
    current_user: UserPayload = RequireMatchReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[TierDistributionResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_match_tier_dist")

    season_repo = MatchSeasonRepository(db)
    if season_id is not None:
        target_season = await season_repo.get_season(season_id)
        if target_season is None:
            raise_player_error(
                PlayerErrorCodes.MATCH_SEASON_NOT_FOUND,
                "指定的赛季不存在",
                request_id,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        target_season_id = target_season.season_id
    else:
        current_season = await season_repo.get_current_season()
        if current_season is None:
            raise_player_error(
                PlayerErrorCodes.NO_ACTIVE_SEASON,
                "当前没有活跃的赛季",
                request_id,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        target_season_id = current_season.season_id

    rating_repo = PlayerRatingRepository(db)
    distribution = await rating_repo.get_tier_distribution(target_season_id)
    total_players = sum(distribution.values())

    items: list[TierDistributionItem] = []
    # 按段位从高到低输出
    tier_order = ["challenger", "master", "diamond", "platinum", "gold", "silver", "bronze"]
    for tier in tier_order:
        count = distribution.get(tier, 0)
        percentage = round(count / total_players * 100, 2) if total_players > 0 else 0.0
        items.append(
            TierDistributionItem(
                tier=MatchTier(tier),
                count=count,
                percentage=percentage,
            )
        )
        set_match_tier_distribution(str(target_season_id), tier, count)

    set_match_season_active_players(str(target_season_id), total_players)
    record_match_tier_distribution_query(str(target_season_id))
    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=str(current_user.user_id),
        operator_role=current_user.role.value,
        action=ACTION_MATCH_TIER_DISTRIBUTION_QUERY,
        resource_type=RESOURCE_PLAYER_RATING,
        resource_id=target_season_id,
        result_status=status.HTTP_200_OK,
    )
    await db.commit()

    return EnvelopeResponse(
        request_id=request_id,
        data=TierDistributionResponse(
            season_id=target_season_id,
            total_players=total_players,
            distribution=items,
        ),
        trace_id=trace_id,
    )


@router.get(
    "/player/match/leaderboard/neighbors",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "No active season or player rating not found"},
    },
    tags=["match"],
)
async def get_leaderboard_neighbors(
    request: Request,
    before: int = Query(default=2, ge=0, le=10),
    after: int = Query(default=2, ge=0, le=10),
    season_id: uuid.UUID | None = Query(default=None, description="指定历史赛季ID"),
    current_user: UserPayload = RequireMatchReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[LeaderboardNeighborsResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_match_neighbors")

    season_repo = MatchSeasonRepository(db)
    if season_id is not None:
        target_season = await season_repo.get_season(season_id)
        if target_season is None:
            raise_player_error(
                PlayerErrorCodes.MATCH_SEASON_NOT_FOUND,
                "指定的赛季不存在",
                request_id,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        target_season_id = target_season.season_id
    else:
        current_season = await season_repo.get_current_season()
        if current_season is None:
            raise_player_error(
                PlayerErrorCodes.NO_ACTIVE_SEASON,
                "当前没有活跃的赛季",
                request_id,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        target_season_id = current_season.season_id

    rating_repo = PlayerRatingRepository(db)
    player_uuid = uuid.UUID(current_user.user_id)
    neighbors, my_rank = await rating_repo.get_neighbors(
        player_uuid, target_season_id, before=before, after=after
    )
    if my_rank is None:
        raise_player_error(
            PlayerErrorCodes.PLAYER_RATING_NOT_FOUND,
            "您在该赛季暂无段位记录",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    start_rank = max(1, my_rank - before)
    items: list[MatchLeaderboardItem] = []
    player_repo = PlayerRepository(db)
    for idx, rating in enumerate(neighbors):
        player = await player_repo.get_player_by_id(rating.player_id)
        player_name = player.display_name if player else ""
        total_matches = rating.wins + rating.losses + rating.draws
        win_rate = rating.wins / total_matches if total_matches > 0 else 0.0
        items.append(
            MatchLeaderboardItem(
                player_id=rating.player_id,
                player_name=player_name,
                tier=MatchTier(rating.tier),
                division=rating.division,
                rating_points=rating.rating_points,
                wins=rating.wins,
                losses=rating.losses,
                win_rate=round(win_rate, 4),
                rank=start_rank + idx,
            )
        )

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=str(current_user.user_id),
        operator_role=current_user.role.value,
        action=ACTION_MATCH_NEIGHBORS_QUERY,
        resource_type=RESOURCE_PLAYER_RATING,
        resource_id=target_season_id,
        result_status=status.HTTP_200_OK,
    )
    await db.commit()

    return EnvelopeResponse(
        request_id=request_id,
        data=LeaderboardNeighborsResponse(
            season_id=target_season_id,
            my_rank=my_rank,
            items=items,
        ),
        trace_id=trace_id,
    )


@router.get(
    "/player/match/rewards",
    responses={
        401: {"description": "Unauthorized"},
    },
    tags=["match"],
)
async def get_my_season_rewards(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireMatchReadScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[SeasonRewardListResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_match_rewards")

    reward_repo = SeasonRewardRepository(db)
    player_uuid = uuid.UUID(current_user.user_id)
    grants, total = await reward_repo.list_grants_by_player(
        player_uuid, limit=limit, offset=offset
    )

    items = [SeasonRewardItem.model_validate(g) for g in grants]

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=str(current_user.user_id),
        operator_role=current_user.role.value,
        action=ACTION_MATCH_REWARD_QUERY,
        resource_type=RESOURCE_MATCH_SEASON_REWARD,
        resource_id=player_uuid,
        result_status=status.HTTP_200_OK,
    )
    await db.commit()

    return EnvelopeResponse(
        request_id=request_id,
        data=SeasonRewardListResponse(items=items, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


# === 运营侧匹配系统 API ===


@ops_router.get(
    "/match/seasons",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["ops-match"],
)
async def list_match_seasons(
    request: Request,
    status_filter: MatchSeasonStatus | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireMatchOpsScope,
) -> EnvelopeResponse[list[MatchSeasonResponse]]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_ops_match_seasons")

    season_repo = MatchSeasonRepository(db)
    seasons, total = await season_repo.list_seasons(
        status=status_filter.value if status_filter else None,
        limit=limit,
        offset=offset,
    )

    season_responses = [MatchSeasonResponse.model_validate(s) for s in seasons]

    return EnvelopeResponse(
        request_id=request_id,
        data=season_responses,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@ops_router.post(
    "/match/seasons",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        409: {"description": "Season already exists"},
    },
    tags=["ops-match"],
)
async def create_match_season(
    body: CreateMatchSeasonRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireMatchOpsScope,
) -> EnvelopeResponse[MatchSeasonResponse]:
    request_id = _make_request_id("req_ops_match_season_create")

    season_repo = MatchSeasonRepository(db)
    existing = await season_repo.get_season_by_key(body.season_key)
    if existing is not None:
        raise_player_error(
            PlayerErrorCodes.MATCH_SEASON_ALREADY_EXISTS,
            f"赛季 {body.season_key} 已存在",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    season = await season_repo.create_season(
        season_key=body.season_key,
        season_name=body.season_name,
        start_at=body.start_at,
        end_at=body.end_at,
        description=body.description,
        reward_config=body.reward_config,
    )

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_MATCH_SEASON_CREATE,
        resource_type=RESOURCE_MATCH_SEASON,
        resource_id=season.season_id,
        request_id=request_id,
        request_payload_jsonb=body.model_dump(mode="json"),
        result_status=201,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=MatchSeasonResponse.model_validate(season),
        trace_id=x_trace_id,
    )


@ops_router.patch(
    "/match/seasons/{season_id}/status",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Season not found"},
        409: {"description": "Invalid status transition"},
    },
    tags=["ops-match"],
)
async def update_match_season_status(
    season_id: uuid.UUID,
    body: UpdateMatchSeasonStatusRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireMatchOpsScope,
) -> EnvelopeResponse[MatchSeasonResponse]:
    request_id = _make_request_id("req_ops_match_season_status")

    season_repo = MatchSeasonRepository(db)
    season = await season_repo.update_season_status(season_id, body.status.value)
    if season is None:
        raise_player_error(
            PlayerErrorCodes.MATCH_SEASON_NOT_FOUND,
            "赛季不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=x_trace_id or _make_request_id("trace"),
        operator_id=current_user.user_id,
        operator_role=current_user.role.value,
        action=ACTION_MATCH_SEASON_STATUS_UPDATE,
        resource_type=RESOURCE_MATCH_SEASON,
        resource_id=season.season_id,
        request_id=request_id,
        request_payload_jsonb={"status": body.status.value},
        result_status=200,
    )

    return EnvelopeResponse(
        request_id=request_id,
        data=MatchSeasonResponse.model_validate(season),
        trace_id=x_trace_id,
    )


@ops_router.post(
    "/match/seasons/{season_id}/settle",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Season not found"},
        409: {"description": "Season not ended or already settled"},
    },
    tags=["ops-match"],
)
async def settle_match_season(
    season_id: uuid.UUID,
    body: SettleSeasonRequest,
    request: Request,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    current_user: UserPayload = RequireMatchOpsScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[SeasonSettlementResponse]:
    trace_id = x_trace_id or f"trace_{uuid.uuid4().hex[:12]}"
    request_id = _make_request_id("req_ops_match_settle")

    season_repo = MatchSeasonRepository(db)
    season = await season_repo.get_season(season_id)
    if season is None:
        raise_player_error(
            PlayerErrorCodes.MATCH_SEASON_NOT_FOUND,
            "赛季不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # 校验赛季状态：必须为 ended 才能结算
    if season.status != "ended":
        raise_player_error(
            PlayerErrorCodes.MATCH_SEASON_NOT_ENDED,
            f"赛季状态为 {season.status}，仅 ended 状态可结算",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    # 校验结算状态：必须为 unsettled 才能开始结算
    if season.settlement_status == "settled":
        # 幂等：返回已有结算结果
        reward_repo = SeasonRewardRepository(db)
        total_grants = await reward_repo.count_grants_by_season(season.season_id)
        rating_repo = PlayerRatingRepository(db)
        distribution = await rating_repo.get_tier_distribution(season.season_id)
        total_players = await rating_repo.count_active_players(season.season_id)

        audit_repo = AuditRepository(db)
        await audit_repo.create_audit_log(
            trace_id=trace_id,
            request_id=request_id,
            operator_id=str(current_user.user_id),
            operator_role=current_user.role.value,
            action=ACTION_MATCH_SEASON_SETTLE,
            resource_type=RESOURCE_MATCH_SEASON,
            resource_id=season.season_id,
            reason="idempotent_replay",
            request_payload_jsonb={"idempotency_key": idempotency_key},
            result_status=status.HTTP_200_OK,
        )
        await db.commit()

        return EnvelopeResponse(
            request_id=request_id,
            data=SeasonSettlementResponse(
                season_id=season.season_id,
                settlement_status=season.settlement_status,
                settled_at=season.settled_at,
                total_grants=total_grants,
                total_players=total_players,
                tier_distribution=distribution,
            ),
            trace_id=trace_id,
        )

    if season.settlement_status == "settling":
        raise_player_error(
            PlayerErrorCodes.MATCH_SEASON_SETTLEMENT_IN_PROGRESS,
            "赛季正在结算中，请稍后查询",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    # 幂等键检查：如已有同幂等键的奖励记录，直接返回
    reward_repo = SeasonRewardRepository(db)
    existing_grant = await reward_repo.get_grant_by_idempotency_key(idempotency_key)
    if existing_grant is not None:
        total_grants = await reward_repo.count_grants_by_season(season.season_id)
        rating_repo = PlayerRatingRepository(db)
        distribution = await rating_repo.get_tier_distribution(season.season_id)
        total_players = await rating_repo.count_active_players(season.season_id)
        return EnvelopeResponse(
            request_id=request_id,
            data=SeasonSettlementResponse(
                season_id=season.season_id,
                settlement_status=season.settlement_status,
                settled_at=season.settled_at,
                total_grants=total_grants,
                total_players=total_players,
                tier_distribution=distribution,
            ),
            trace_id=trace_id,
        )

    # 标记为结算中
    await season_repo.update_settlement_status(season.season_id, "settling")

    # 列出该赛季所有段位记录（按排名顺序）
    rating_repo = PlayerRatingRepository(db)
    ratings = await rating_repo.list_all_ratings_for_settlement(
        season.season_id, limit=body.batch_size, offset=0
    )

    # 默认奖励配置：按段位发放
    default_reward_config = body.reward_config or season.reward_jsonb or {
        "challenger": {"title": "挑战者之星", "currency": 5000},
        "master": {"title": "宗师之力", "currency": 3000},
        "diamond": {"title": "钻石之辉", "currency": 2000},
        "platinum": {"title": "铂金之光", "currency": 1000},
        "gold": {"title": "黄金之耀", "currency": 500},
        "silver": {"title": "白银之翼", "currency": 200},
        "bronze": {"title": "青铜之心", "currency": 100},
    }

    # 为每个有段位的玩家创建奖励发放记录
    grants_created = 0
    for rank_idx, rating in enumerate(ratings, start=1):
        tier_reward = default_reward_config.get(rating.tier, {})
        # 排名前 10 的玩家额外奖励
        if rank_idx <= 10:
            tier_reward = {
                **tier_reward,
                "rank_bonus": {
                    "rank": rank_idx,
                    "extra_currency": max(0, 1100 - rank_idx * 100),
                },
            }
        try:
            await reward_repo.create_grant(
                season_id=season.season_id,
                player_id=rating.player_id,
                final_rank=rank_idx,
                final_tier=rating.tier,
                final_division=rating.division,
                final_rating_points=rating.rating_points,
                reward_payload=tier_reward,
                idempotency_key=f"sr_{season.season_id}_{rating.player_id}",
                trace_id=trace_id,
                status="granted",
            )
            record_match_season_reward_grant(str(season.season_id), rating.tier)
            grants_created += 1
        except Exception:
            # 单个玩家奖励发放失败不阻断整体结算，记录为 failed 状态
            await reward_repo.create_grant(
                season_id=season.season_id,
                player_id=rating.player_id,
                final_rank=rank_idx,
                final_tier=rating.tier,
                final_division=rating.division,
                final_rating_points=rating.rating_points,
                reward_payload=tier_reward,
                idempotency_key=f"sr_{season.season_id}_{rating.player_id}_retry",
                trace_id=trace_id,
                status="failed",
            )

    # 标记为已结算
    await season_repo.update_settlement_status(season.season_id, "settled")

    # 重新查询最终分布
    distribution = await rating_repo.get_tier_distribution(season.season_id)
    total_players = await rating_repo.count_active_players(season.season_id)
    total_grants = await reward_repo.count_grants_by_season(season.season_id)

    record_match_season_settlement(str(season.season_id))
    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=str(current_user.user_id),
        operator_role=current_user.role.value,
        action=ACTION_MATCH_SEASON_SETTLE,
        resource_type=RESOURCE_MATCH_SEASON,
        resource_id=season.season_id,
        request_payload_jsonb={
            "idempotency_key": idempotency_key,
            "batch_size": body.batch_size,
            "grants_created": grants_created,
        },
        result_status=status.HTTP_200_OK,
    )
    await db.commit()

    return EnvelopeResponse(
        request_id=request_id,
        data=SeasonSettlementResponse(
            season_id=season.season_id,
            settlement_status="settled",
            settled_at=season.settled_at,
            total_grants=total_grants,
            total_players=total_players,
            tier_distribution=distribution,
        ),
        trace_id=trace_id,
    )


@ops_router.get(
    "/match/seasons/{season_id}/rewards",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Season or rewards not found"},
    },
    tags=["ops-match"],
)
async def list_season_rewards(
    season_id: uuid.UUID,
    request: Request,
    status_filter: str | None = Query(default=None, description="按状态过滤：pending/granted/failed"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPayload = RequireMatchOpsScope,
    db: AsyncSession = Depends(get_db),
) -> EnvelopeResponse[SeasonRewardListResponse]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_ops_match_rewards")

    season_repo = MatchSeasonRepository(db)
    season = await season_repo.get_season(season_id)
    if season is None:
        raise_player_error(
            PlayerErrorCodes.MATCH_SEASON_NOT_FOUND,
            "赛季不存在",
            request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    reward_repo = SeasonRewardRepository(db)
    grants, total = await reward_repo.list_grants_by_season(
        season.season_id, status=status_filter, limit=limit, offset=offset
    )

    items = [SeasonRewardItem.model_validate(g) for g in grants]

    audit_repo = AuditRepository(db)
    await audit_repo.create_audit_log(
        trace_id=trace_id,
        request_id=request_id,
        operator_id=str(current_user.user_id),
        operator_role=current_user.role.value,
        action=ACTION_MATCH_REWARD_GRANT,
        resource_type=RESOURCE_MATCH_SEASON_REWARD,
        resource_id=season.season_id,
        result_status=status.HTTP_200_OK,
    )
    await db.commit()

    return EnvelopeResponse(
        request_id=request_id,
        data=SeasonRewardListResponse(items=items, total=total),
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@ops_router.get(
    "/match/queues",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["ops-match"],
)
async def list_match_queues(
    request: Request,
    season_id: uuid.UUID | None = Query(default=None),
    status_filter: MatchQueueStatus | None = Query(default=None),
    match_mode: MatchMode | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireMatchOpsScope,
) -> EnvelopeResponse[list[MatchQueueResponse]]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_ops_match_queues")

    queue_repo = MatchQueueRepository(db)
    queues, total = await queue_repo.list_queues(
        season_id=season_id,
        status=status_filter.value if status_filter else None,
        match_mode=match_mode.value if match_mode else None,
        limit=limit,
        offset=offset,
    )

    queue_responses = [MatchQueueResponse.model_validate(q) for q in queues]

    return EnvelopeResponse(
        request_id=request_id,
        data=queue_responses,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@ops_router.get(
    "/match/rooms",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["ops-match"],
)
async def list_match_rooms(
    request: Request,
    season_id: uuid.UUID | None = Query(default=None),
    status_filter: MatchRoomStatus | None = Query(default=None),
    player_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireMatchOpsScope,
) -> EnvelopeResponse[list[MatchRoomResponse]]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_ops_match_rooms")

    room_repo = MatchRoomRepository(db)
    rooms, total = await room_repo.list_rooms(
        season_id=season_id,
        status=status_filter.value if status_filter else None,
        player_id=player_id,
        limit=limit,
        offset=offset,
    )

    room_responses = [MatchRoomResponse.model_validate(r) for r in rooms]

    return EnvelopeResponse(
        request_id=request_id,
        data=room_responses,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )


@ops_router.get(
    "/match/results",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
    tags=["ops-match"],
)
async def list_match_results(
    request: Request,
    season_id: uuid.UUID | None = Query(default=None),
    player_id: uuid.UUID | None = Query(default=None),
    match_mode: MatchMode | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: UserPayload = RequireMatchOpsScope,
) -> EnvelopeResponse[list[MatchResultResponse]]:
    trace_id = _get_trace_id(request)
    request_id = _make_request_id("req_ops_match_results")

    result_repo = MatchResultRepository(db)
    results, total = await result_repo.list_results(
        season_id=season_id,
        player_id=player_id,
        match_mode=match_mode.value if match_mode else None,
        limit=limit,
        offset=offset,
    )

    result_responses = [MatchResultResponse.model_validate(r) for r in results]

    return EnvelopeResponse(
        request_id=request_id,
        data=result_responses,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
        trace_id=trace_id,
    )
