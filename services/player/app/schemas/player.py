import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class QuestStatus(str, Enum):
    AVAILABLE = "available"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class ContributionSource(str, Enum):
    QUEST = "quest"
    VOTE = "vote"
    BUILDING = "building"
    OPS = "ops"
    SYSTEM = "system"


class AchievementRarity(str, Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class AchievementCategory(str, Enum):
    QUEST = "quest"
    EXPLORATION = "exploration"
    COMBAT = "combat"
    REPUTATION = "reputation"
    VOTE = "vote"
    SOCIAL = "social"
    COLLECTION = "collection"


class AchievementSource(str, Enum):
    QUEST = "quest"
    EXPLORATION = "exploration"
    COMBAT = "combat"
    REPUTATION = "reputation"
    VOTE = "vote"
    OPS = "ops"
    SYSTEM = "system"


VALID_ACHIEVEMENT_RARITIES = {r.value for r in AchievementRarity}
VALID_ACHIEVEMENT_CATEGORIES = {c.value for c in AchievementCategory}


class ReputationLevel(str, Enum):
    HOSTILE = "hostile"
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    HONORED = "honored"
    REVERED = "revered"
    EXALTED = "exalted"


REPUTATION_LEVEL_THRESHOLDS: dict[str, int] = {
    "hostile": -3000,
    "neutral": 0,
    "friendly": 3000,
    "honored": 9000,
    "revered": 21000,
    "exalted": 42000,
}


def get_reputation_level(reputation: int) -> ReputationLevel:
    if reputation < REPUTATION_LEVEL_THRESHOLDS["neutral"]:
        return ReputationLevel.HOSTILE
    elif reputation < REPUTATION_LEVEL_THRESHOLDS["friendly"]:
        return ReputationLevel.NEUTRAL
    elif reputation < REPUTATION_LEVEL_THRESHOLDS["honored"]:
        return ReputationLevel.FRIENDLY
    elif reputation < REPUTATION_LEVEL_THRESHOLDS["revered"]:
        return ReputationLevel.HONORED
    elif reputation < REPUTATION_LEVEL_THRESHOLDS["exalted"]:
        return ReputationLevel.REVERED
    else:
        return ReputationLevel.EXALTED


class UnlockType(str, Enum):
    REGION_UNLOCK = "region_unlock"
    QUEST_VISIBLE = "quest_visible"
    NPC_INTERACTION = "npc_interaction"


class ReputationUnlockCondition(BaseModel):
    unlock_type: UnlockType
    required_level: ReputationLevel | None = None
    min_reputation: int | None = None
    region_id: str | None = None


DEFAULT_REGION_UNLOCK_THRESHOLD = REPUTATION_LEVEL_THRESHOLDS["friendly"]


def check_reputation_unlock(
    current_reputation: int,
    condition: ReputationUnlockCondition,
) -> bool:
    if condition.min_reputation is not None:
        if current_reputation < condition.min_reputation:
            return False
    if condition.required_level is not None:
        required_threshold = REPUTATION_LEVEL_THRESHOLDS[condition.required_level.value]
        if current_reputation < required_threshold:
            return False
    return True


def get_next_unlock_threshold(
    current_reputation: int,
    thresholds: list[int] | None = None,
) -> tuple[int, float]:
    if thresholds is None:
        thresholds = sorted(REPUTATION_LEVEL_THRESHOLDS.values())
    thresholds = sorted(thresholds)
    next_threshold = thresholds[-1]
    for t in thresholds:
        if t > current_reputation:
            next_threshold = t
            break
    prev_threshold = 0
    for t in reversed(thresholds):
        if t <= current_reputation:
            prev_threshold = t
            break
    progress_range = next_threshold - prev_threshold
    if progress_range <= 0:
        progress = 1.0
    else:
        current_progress = current_reputation - prev_threshold
        progress = min(1.0, max(0.0, current_progress / progress_range))
    return next_threshold, progress


class ErrorDetail(BaseModel):
    location: str
    field: str
    issue: str
    rejected_value: object | None = None


class ErrorResponse(BaseModel):
    code: str
    message: str
    request_id: str
    details: list[ErrorDetail] | None = None


class HealthResponse(BaseModel):
    service: str
    version: str
    status: str = "ok"


class PlayerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    player_id: uuid.UUID
    display_name: str
    chapter_id: str | None = None
    level: int = 1
    experience_points: int = 0
    contribution_points: int = 0
    reputation_snapshot: dict | None = None
    progress_jsonb: dict | None = None
    created_at: datetime
    updated_at: datetime


class CreatePlayerRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=128)
    chapter_id: str | None = None


class UpdatePlayerRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=128)
    chapter_id: str | None = None


class PlayerQuestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    player_quest_id: uuid.UUID
    quest_id: str
    status: QuestStatus
    objectives_jsonb: dict | None = None
    rewards_jsonb: dict | None = None
    created_at: datetime
    updated_at: datetime


class AcceptQuestRequest(BaseModel):
    pass


class UpdateQuestProgressRequest(BaseModel):
    objectives: dict[str, object] = Field(default_factory=dict)


class CompleteQuestRequest(BaseModel):
    pass


class FailQuestRequest(BaseModel):
    pass


class CreatePlayerQuestRequest(BaseModel):
    quest_id: str = Field(min_length=1, max_length=128)
    status: QuestStatus = QuestStatus.AVAILABLE
    objectives_jsonb: dict | None = None
    rewards_jsonb: dict | None = None


class UpdateQuestStatusRequest(BaseModel):
    status: QuestStatus


class PlayerRegionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    player_region_id: uuid.UUID
    region_id: str
    unlocked_at: datetime | None = None
    reputation: int = 0
    reputation_level: ReputationLevel = ReputationLevel.NEUTRAL
    created_at: datetime

    @classmethod
    def model_validate(cls, obj: Any, *args: Any, **kwargs: Any) -> "PlayerRegionResponse":
        if hasattr(obj, "reputation") and isinstance(obj.reputation, int):
            level = get_reputation_level(obj.reputation)
            obj_dict = {
                "player_region_id": obj.player_region_id,
                "region_id": obj.region_id,
                "unlocked_at": obj.unlocked_at,
                "reputation": obj.reputation,
                "reputation_level": level,
                "created_at": obj.created_at,
            }
            return super().model_validate(obj_dict, *args, **kwargs)
        return super().model_validate(obj, *args, **kwargs)


class RegionReputationResponse(BaseModel):
    region_id: str
    reputation: int
    reputation_level: ReputationLevel
    next_level_threshold: int
    current_level_progress: float


class AdjustReputationRequest(BaseModel):
    amount: int = Field(ge=-50000, le=50000)
    reason: str | None = Field(default=None, max_length=256)


class ItemType(str, Enum):
    CONSUMABLE = "consumable"
    EQUIPMENT = "equipment"
    MATERIAL = "material"
    QUEST_ITEM = "quest_item"


class InventoryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inventory_id: uuid.UUID
    item_key: str
    item_type: str
    quantity: int
    metadata_jsonb: dict | None = None
    created_at: datetime
    updated_at: datetime


class AddItemRequest(BaseModel):
    item_key: str = Field(min_length=1, max_length=128)
    item_type: ItemType = ItemType.MATERIAL
    quantity: int = Field(default=1, ge=1)
    metadata_jsonb: dict | None = None


class RemoveItemRequest(BaseModel):
    quantity: int = Field(default=1, ge=1)


class UseItemRequest(BaseModel):
    quantity: int = Field(default=1, ge=1)


class ContributionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    contribution_id: uuid.UUID
    player_id: uuid.UUID
    amount: int
    source: ContributionSource
    source_id: str | None = None
    description: str | None = None
    created_at: datetime


class ContributionListResponse(BaseModel):
    contribution_points: int
    contributions: list[ContributionResponse]
    total: int


class AddContributionRequest(BaseModel):
    amount: int = Field(ge=1)
    source: ContributionSource
    source_id: str | None = None
    description: str | None = None


class PaginatedMeta(BaseModel):
    total: int
    limit: int
    offset: int


class AchievementDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    achievement_key: str
    name: str
    description: str
    icon: str | None = None
    rarity: AchievementRarity
    category: AchievementCategory
    points: int
    reward_jsonb: dict | None = None
    condition_jsonb: dict | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AchievementDefinitionListResponse(BaseModel):
    achievements: list[AchievementDefinitionResponse]
    total: int


class CreateAchievementRequest(BaseModel):
    achievement_key: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=128)
    description: str = Field(min_length=1)
    rarity: AchievementRarity
    category: AchievementCategory
    points: int = Field(ge=0, default=10)
    icon: str | None = Field(default=None, max_length=256)
    reward_jsonb: dict | None = None
    condition_jsonb: dict | None = None


class PlayerAchievementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    player_achievement_id: uuid.UUID
    player_id: uuid.UUID
    achievement_key: str
    unlocked_at: datetime
    reward_claimed: bool
    claimed_at: datetime | None = None
    source: AchievementSource
    source_id: str | None = None


class PlayerAchievementListResponse(BaseModel):
    achievements: list[PlayerAchievementResponse]
    total: int


class UnlockAchievementRequest(BaseModel):
    source: AchievementSource = AchievementSource.SYSTEM
    source_id: str | None = None


class PlayerProfileResponse(BaseModel):
    """玩家完整信息聚合响应"""

    player_id: uuid.UUID
    display_name: str
    chapter_id: str | None = None
    level: int = 1
    experience_points: int = 0
    next_level_experience: int = 0
    level_progress: float = 0.0
    contribution_points: int = 0
    reputation_summary: list[RegionReputationResponse] = []
    achievements_unlocked: int = 0
    achievements_total: int = 0
    created_at: datetime
    updated_at: datetime


MAX_PLAYER_LEVEL = 60
BASE_EXPERIENCE = 100
EXPERIENCE_GROWTH_RATE = 1.15


def get_experience_for_level(level: int) -> int:
    if level <= 1:
        return 0
    level = min(level, MAX_PLAYER_LEVEL + 1)
    total_exp = 0
    for i in range(1, level):
        total_exp += int(BASE_EXPERIENCE * (EXPERIENCE_GROWTH_RATE ** (i - 1)))
    return total_exp


def get_level_from_experience(exp: int) -> int:
    if exp < 0:
        return 1
    level = 1
    cumulative_exp = 0
    while level <= MAX_PLAYER_LEVEL:
        next_level_exp = int(BASE_EXPERIENCE * (EXPERIENCE_GROWTH_RATE ** (level - 1)))
        if cumulative_exp + next_level_exp > exp:
            break
        cumulative_exp += next_level_exp
        level += 1
    return min(level, MAX_PLAYER_LEVEL)


def get_level_progress(exp: int) -> tuple[int, int, float]:
    level = get_level_from_experience(exp)
    if level >= MAX_PLAYER_LEVEL:
        return level, get_experience_for_level(level), 1.0
    current_level_exp = get_experience_for_level(level)
    next_level_exp = get_experience_for_level(level + 1)
    progress_range = next_level_exp - current_level_exp
    if progress_range <= 0:
        return level, next_level_exp, 1.0
    current_progress = exp - current_level_exp
    progress = min(1.0, max(0.0, current_progress / progress_range))
    return level, next_level_exp, progress


def calculate_level_up_rewards(new_level: int) -> dict[str, int]:
    rewards: dict[str, int] = {}
    rewards["contribution_points"] = new_level * 10
    return rewards


class ExperienceSource(str, Enum):
    QUEST = "quest"
    COMBAT = "combat"
    EXPLORATION = "exploration"
    ACHIEVEMENT = "achievement"
    OPS = "ops"
    SYSTEM = "system"


VALID_EXPERIENCE_SOURCES = {s.value for s in ExperienceSource}


class PlayerLevelResponse(BaseModel):
    player_id: uuid.UUID
    level: int
    experience_points: int
    next_level_experience: int
    level_progress: float
    updated_at: datetime


class AddExperienceRequest(BaseModel):
    amount: int = Field(ge=1, le=100000)
    source: ExperienceSource = ExperienceSource.SYSTEM
    source_id: str | None = Field(default=None, max_length=128)
    reason: str | None = Field(default=None, max_length=256)


class EnvelopeResponse(BaseModel, Generic[T]):
    request_id: str
    data: T
    meta: PaginatedMeta | None = None
    trace_id: str | None = None


class FriendshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"


# === 私聊消息相关 Schema ===


class SendMessageRequest(BaseModel):
    receiver_id: uuid.UUID
    content: str = Field(min_length=1, max_length=500)


class PrivateMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: uuid.UUID
    sender_id: uuid.UUID
    receiver_id: uuid.UUID
    content: str
    is_read: bool
    created_at: datetime


class ConversationResponse(BaseModel):
    friend_id: uuid.UUID
    latest_message: PrivateMessageResponse | None = None


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]


class MessageListResponse(BaseModel):
    messages: list[PrivateMessageResponse]


class UnreadCountResponse(BaseModel):
    unread_count: int


class SendFriendRequestRequest(BaseModel):
    friend_id: uuid.UUID


class AcceptFriendRequestRequest(BaseModel):
    player_id: uuid.UUID


class RejectFriendRequestRequest(BaseModel):
    player_id: uuid.UUID


class FriendshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    friendship_id: uuid.UUID
    player_id: uuid.UUID
    friend_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime


class FriendListItemResponse(BaseModel):
    """好友列表中的单项，包含好友玩家信息"""

    friendship_id: uuid.UUID
    friend_id: uuid.UUID
    friend_display_name: str
    friend_level: int = 1
    status: str
    created_at: datetime
    updated_at: datetime


class FriendListResponse(BaseModel):
    friends: list[FriendListItemResponse]
    total: int


class FriendRequestItemResponse(BaseModel):
    """待处理好友请求中的单项"""

    friendship_id: uuid.UUID
    player_id: uuid.UUID
    player_display_name: str
    player_level: int = 1
    status: str
    created_at: datetime
    updated_at: datetime


class FriendRequestListResponse(BaseModel):
    requests: list[FriendRequestItemResponse]
    total: int


class FriendStatusResponse(BaseModel):
    friendship_id: uuid.UUID | None = None
    player_id: uuid.UUID | None = None
    friend_id: uuid.UUID | None = None
    status: str = "none"


# === 公会相关 Schema ===


class GuildMemberRole(str, Enum):
    LEADER = "leader"
    OFFICER = "officer"
    MEMBER = "member"


class CreateGuildRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=500)
    max_members: int = Field(default=50, ge=1, le=200)


class UpdateGuildRequest(BaseModel):
    description: str | None = Field(default=None, max_length=500)
    announcement: str | None = Field(default=None, max_length=500)


class AddGuildMemberRequest(BaseModel):
    player_id: uuid.UUID


class TransferLeaderRequest(BaseModel):
    new_leader_id: uuid.UUID


class GuildResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    guild_id: uuid.UUID
    name: str
    leader_id: uuid.UUID
    description: str | None = None
    announcement: str | None = None
    level: int
    member_count: int
    max_members: int
    created_at: datetime
    updated_at: datetime


class GuildMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    guild_member_id: uuid.UUID
    guild_id: uuid.UUID
    player_id: uuid.UUID
    role: str
    joined_at: datetime


class GuildMemberListItemResponse(BaseModel):
    """公会成员列表中的单项，包含玩家信息"""

    guild_member_id: uuid.UUID
    player_id: uuid.UUID
    player_display_name: str = ""
    player_level: int = 1
    role: str
    joined_at: datetime


class GuildMemberListResponse(BaseModel):
    members: list[GuildMemberListItemResponse]
    total: int


# === 社交数据聚合 Schema ===


class GuildSummary(BaseModel):
    """公会摘要信息"""

    guild_id: uuid.UUID
    name: str
    level: int
    member_count: int
    my_role: str  # leader/officer/member


class FriendSummary(BaseModel):
    """好友摘要信息"""

    player_id: uuid.UUID
    player_name: str
    level: int
    online: bool = False


class SocialOverview(BaseModel):
    """社交概览响应"""

    friends_count: int  # 好友总数
    pending_requests: int  # 待处理好友请求数
    unread_messages: int  # 未读消息数
    guild_info: GuildSummary | None = None  # 公会信息（如果已加入）
    recent_friends: list[FriendSummary] = []  # 最近好友列表（最多5个）
