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
