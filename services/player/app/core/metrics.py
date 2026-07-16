"""player-service 业务指标定义。

使用 prometheus_client 定义业务指标，由 routes 层在关键操作发生时更新。
"""

from prometheus_client import Counter, Gauge

# 玩家总数
PLAYERS_TOTAL = Gauge(
    "players_total",
    "玩家总数",
)

# 玩家操作数（按动作类型分组：create、update、unlock_region）
PLAYER_OPERATIONS_TOTAL = Counter(
    "player_operations_total",
    "玩家操作数（按动作类型）",
    labelnames=["action"],
)

# 任务数（按状态分组的当前值）
PLAYER_QUESTS_BY_STATUS = Gauge(
    "player_quests_by_status",
    "任务数（按状态）",
    labelnames=["status"],
)

# 贡献度发放次数（按玩家、来源分组）
CONTRIBUTION_ADDITIONS_TOTAL = Counter(
    "contribution_additions_total",
    "贡献度发放次数",
    labelnames=["player_id", "source"],
)


def record_player_create() -> None:
    """记录一次玩家创建。"""
    PLAYER_OPERATIONS_TOTAL.labels(action="create").inc()


def record_player_update() -> None:
    """记录一次玩家更新。"""
    PLAYER_OPERATIONS_TOTAL.labels(action="update").inc()


def record_player_region_unlock() -> None:
    """记录一次区域解锁。"""
    PLAYER_OPERATIONS_TOTAL.labels(action="unlock_region").inc()


def record_quest_accept() -> None:
    """记录一次任务接取。"""
    PLAYER_OPERATIONS_TOTAL.labels(action="quest_accept").inc()


def record_quest_complete() -> None:
    """记录一次任务完成。"""
    PLAYER_OPERATIONS_TOTAL.labels(action="quest_complete").inc()


def record_quest_fail() -> None:
    """记录一次任务失败。"""
    PLAYER_OPERATIONS_TOTAL.labels(action="quest_fail").inc()


def record_quest_progress_update() -> None:
    """记录一次任务进度更新。"""
    PLAYER_OPERATIONS_TOTAL.labels(action="quest_progress_update").inc()


def record_inventory_add() -> None:
    """记录一次背包添加物品。"""
    PLAYER_OPERATIONS_TOTAL.labels(action="inventory_add").inc()


def record_inventory_remove() -> None:
    """记录一次背包移除物品。"""
    PLAYER_OPERATIONS_TOTAL.labels(action="inventory_remove").inc()


def record_inventory_use() -> None:
    """记录一次背包使用物品。"""
    PLAYER_OPERATIONS_TOTAL.labels(action="inventory_use").inc()


def record_reputation_add() -> None:
    """记录一次声望增加。"""
    PLAYER_OPERATIONS_TOTAL.labels(action="reputation_add").inc()


def record_reputation_remove() -> None:
    """记录一次声望减少。"""
    PLAYER_OPERATIONS_TOTAL.labels(action="reputation_remove").inc()


def record_reputation_unlock() -> None:
    """记录一次声望解锁。"""
    PLAYER_OPERATIONS_TOTAL.labels(action="reputation_unlock").inc()


def set_players_total(count: int) -> None:
    """设置玩家总数。"""
    PLAYERS_TOTAL.set(count)


def set_player_quests_by_status(status_counts: dict[str, int]) -> None:
    """设置按状态分组的任务数。

    Args:
        status_counts: 状态到数量的映射，例如 {"available": 1, "active": 2}
    """
    for status_label in ("available", "active", "completed", "failed"):
        PLAYER_QUESTS_BY_STATUS.labels(status=status_label).set(
            status_counts.get(status_label, 0)
        )


def record_contribution_add(player_id: str, source: str, amount: int) -> None:
    """记录一次贡献度发放。

    Args:
        player_id: 玩家ID
        source: 贡献度来源
        amount: 发放数量
    """
    CONTRIBUTION_ADDITIONS_TOTAL.labels(player_id=player_id, source=source).inc(amount)


ACHIEVEMENTS_UNLOCKED_TOTAL = Counter(
    "achievements_unlocked_total",
    "成就解锁次数",
    labelnames=["player_id", "category"],
)

ACHIEVEMENTS_REWARD_CLAIMED_TOTAL = Counter(
    "achievements_reward_claimed_total",
    "成就奖励领取次数",
    labelnames=["player_id", "achievement_key"],
)


def record_achievement_unlocked(player_id: str, category: str) -> None:
    """记录一次成就解锁。

    Args:
        player_id: 玩家ID
        category: 成就类别
    """
    ACHIEVEMENTS_UNLOCKED_TOTAL.labels(player_id=player_id, category=category).inc()


def record_achievement_reward_claimed(player_id: str, achievement_key: str) -> None:
    """记录一次成就奖励领取。

    Args:
        player_id: 玩家ID
        achievement_key: 成就键
    """
    ACHIEVEMENTS_REWARD_CLAIMED_TOTAL.labels(
        player_id=player_id, achievement_key=achievement_key
    ).inc()


EXPERIENCE_GAINED_TOTAL = Counter(
    "experience_gained_total",
    "经验值获得总量",
    labelnames=["player_id", "source"],
)

LEVEL_UPS_TOTAL = Counter(
    "level_ups_total",
    "升级次数",
    labelnames=["player_id", "level"],
)


def record_experience_gained(player_id: str, source: str, amount: int) -> None:
    """记录一次经验值获得。

    Args:
        player_id: 玩家ID
        source: 经验来源
        amount: 获得数量
    """
    EXPERIENCE_GAINED_TOTAL.labels(player_id=player_id, source=source).inc(amount)


def record_level_up(player_id: str, level: int) -> None:
    """记录一次升级。

    Args:
        player_id: 玩家ID
        level: 达到的等级
    """
    LEVEL_UPS_TOTAL.labels(player_id=player_id, level=str(level)).inc()


FRIEND_REQUESTS_SENT_TOTAL = Counter(
    "friend_requests_sent_total",
    "好友请求发送次数",
    labelnames=["player_id"],
)

FRIEND_REQUESTS_ACCEPTED_TOTAL = Counter(
    "friend_requests_accepted_total",
    "好友请求接受次数",
    labelnames=["player_id"],
)


def record_friend_request_sent(player_id: str) -> None:
    """记录一次好友请求发送。

    Args:
        player_id: 发送者ID
    """
    FRIEND_REQUESTS_SENT_TOTAL.labels(player_id=player_id).inc()


def record_friend_request_accepted(player_id: str) -> None:
    """记录一次好友请求接受。

    Args:
        player_id: 接受者ID
    """
    FRIEND_REQUESTS_ACCEPTED_TOTAL.labels(player_id=player_id).inc()


PRIVATE_MESSAGES_SENT_TOTAL = Counter(
    "private_messages_sent_total",
    "私聊消息发送次数",
    labelnames=["sender_id", "receiver_id"],
)

PRIVATE_MESSAGES_READ_TOTAL = Counter(
    "private_messages_read_total",
    "私聊消息已读次数",
    labelnames=["receiver_id"],
)


def record_private_message_sent(sender_id: str, receiver_id: str) -> None:
    """记录一次私聊消息发送。

    Args:
        sender_id: 发送者ID
        receiver_id: 接收者ID
    """
    PRIVATE_MESSAGES_SENT_TOTAL.labels(sender_id=sender_id, receiver_id=receiver_id).inc()


def record_private_message_read(receiver_id: str) -> None:
    """记录一次私聊消息已读。

    Args:
        receiver_id: 接收者ID
    """
    PRIVATE_MESSAGES_READ_TOTAL.labels(receiver_id=receiver_id).inc()


# 公会相关指标
GUILDS_CREATED_TOTAL = Counter(
    "guilds_created_total",
    "公会创建次数",
    labelnames=["leader_id"],
)

GUILD_MEMBERS_ADDED_TOTAL = Counter(
    "guild_members_added_total",
    "公会成员加入次数",
    labelnames=["guild_id"],
)

GUILD_MEMBERS_REMOVED_TOTAL = Counter(
    "guild_members_removed_total",
    "公会成员移除次数",
    labelnames=["guild_id"],
)


def record_guild_created(leader_id: str) -> None:
    """记录一次公会创建。

    Args:
        leader_id: 会长ID
    """
    GUILDS_CREATED_TOTAL.labels(leader_id=leader_id).inc()


def record_guild_member_added(guild_id: str) -> None:
    """记录一次公会成员加入。

    Args:
        guild_id: 公会ID
    """
    GUILD_MEMBERS_ADDED_TOTAL.labels(guild_id=guild_id).inc()


def record_guild_member_removed(guild_id: str) -> None:
    """记录一次公会成员移除。

    Args:
        guild_id: 公会ID
    """
    GUILD_MEMBERS_REMOVED_TOTAL.labels(guild_id=guild_id).inc()


GUILD_MESSAGES_SENT_TOTAL = Counter(
    "guild_messages_sent_total",
    "公会消息发送次数",
    labelnames=["guild_id", "sender_id"],
)

GUILD_MESSAGES_READ_TOTAL = Counter(
    "guild_messages_read_total",
    "公会消息已读次数",
    labelnames=["guild_id", "player_id"],
)


def record_guild_message_sent(guild_id: str, sender_id: str) -> None:
    """记录一次公会消息发送。

    Args:
        guild_id: 公会ID
        sender_id: 发送者ID
    """
    GUILD_MESSAGES_SENT_TOTAL.labels(guild_id=guild_id, sender_id=sender_id).inc()


def record_guild_message_read(guild_id: str, player_id: str) -> None:
    """记录一次公会消息已读。

    Args:
        guild_id: 公会ID
        player_id: 玩家ID
    """
    GUILD_MESSAGES_READ_TOTAL.labels(guild_id=guild_id, player_id=player_id).inc()


# 装备相关指标
EQUIPMENT_OPERATIONS_TOTAL = Counter(
    "equipment_operations_total",
    "装备操作次数（按动作类型）",
    labelnames=["action"],
)

EQUIPPED_ITEMS_BY_SLOT = Gauge(
    "equipped_items_by_slot",
    "装备物品数（按槽位）",
    labelnames=["slot"],
)


def record_equipment_equip() -> None:
    """记录一次装备穿戴。"""
    EQUIPMENT_OPERATIONS_TOTAL.labels(action="equip").inc()


def record_equipment_unequip() -> None:
    """记录一次装备卸下。"""
    EQUIPMENT_OPERATIONS_TOTAL.labels(action="unequip").inc()


# 公会战相关指标
GUILD_WARS_DECLARED_TOTAL = Counter(
    "guild_wars_declared_total",
    "公会战宣战次数",
    labelnames=["challenger_guild_id"],
)

GUILD_WARS_COMPLETED_TOTAL = Counter(
    "guild_wars_completed_total",
    "公会战完成次数",
    labelnames=["winner_guild_id"],
)

GUILD_WAR_PARTICIPANTS_JOINED_TOTAL = Counter(
    "guild_war_participants_joined_total",
    "公会战参与加入次数",
    labelnames=["war_id"],
)


def record_guild_war_declared(challenger_guild_id: str) -> None:
    """记录一次公会战宣战。"""
    GUILD_WARS_DECLARED_TOTAL.labels(challenger_guild_id=challenger_guild_id).inc()


def record_guild_war_completed(winner_guild_id: str) -> None:
    """记录一次公会战完成。"""
    GUILD_WARS_COMPLETED_TOTAL.labels(winner_guild_id=winner_guild_id).inc()


def record_guild_war_participant_joined(war_id: str) -> None:
    """记录一次公会战参与加入。"""
    GUILD_WAR_PARTICIPANTS_JOINED_TOTAL.labels(war_id=war_id).inc()


# 好友协作任务相关指标
COLLAB_QUESTS_CREATED_TOTAL = Counter(
    "collab_quests_created_total",
    "好友协作任务创建次数",
    labelnames=["initiator_id"],
)

COLLAB_QUESTS_COMPLETED_TOTAL = Counter(
    "collab_quests_completed_total",
    "好友协作任务完成次数",
    labelnames=["initiator_id"],
)


def record_collab_quest_created(initiator_id: str) -> None:
    """记录一次好友协作任务创建。"""
    COLLAB_QUESTS_CREATED_TOTAL.labels(initiator_id=initiator_id).inc()


def record_collab_quest_completed(initiator_id: str) -> None:
    """记录一次好友协作任务完成。"""
    COLLAB_QUESTS_COMPLETED_TOTAL.labels(initiator_id=initiator_id).inc()
