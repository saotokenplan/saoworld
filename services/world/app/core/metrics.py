"""world-service 业务指标定义。"""

from prometheus_client import Counter, Gauge

# 区域操作次数（按动作类型分组：create、status_update）
WORLD_REGION_OPERATIONS_TOTAL = Counter(
    "world_region_operations_total",
    "区域操作次数（按动作类型）",
    labelnames=["action"],
)

# 区域状态迁移次数（按 from_status/to_status 分组）
WORLD_REGION_TRANSITIONS_TOTAL = Counter(
    "world_region_transitions_total",
    "区域状态迁移次数",
    labelnames=["from_status", "to_status"],
)

# 区域数（按状态分组的 Gauge）
WORLD_REGIONS_BY_STATUS = Gauge(
    "world_regions_by_status",
    "区域数（按状态）",
    labelnames=["status"],
)

# NPC 操作次数（按动作类型分组）
WORLD_NPC_OPERATIONS_TOTAL = Counter(
    "world_npc_operations_total",
    "NPC 操作次数（按动作类型）",
    labelnames=["action"],
)

# 当前 NPC 数（按章节分组的 Gauge）
WORLD_NPCS_BY_CHAPTER = Gauge(
    "world_npcs_by_chapter",
    "NPC 数（按章节）",
    labelnames=["chapter_id"],
)

# Quest 操作次数（按动作类型分组）
WORLD_QUEST_OPERATIONS_TOTAL = Counter(
    "world_quest_operations_total",
    "Quest 操作次数（按动作类型）",
    labelnames=["action"],
)

# 当前 Quest 数（按类型分组的 Gauge）
WORLD_QUESTS_BY_TYPE = Gauge(
    "world_quests_by_type",
    "Quest 数（按任务类型）",
    labelnames=["quest_type"],
)


def record_region_create() -> None:
    """记录一次区域创建。"""
    WORLD_REGION_OPERATIONS_TOTAL.labels(action="create").inc()


def record_region_status_transition(from_status: str, to_status: str) -> None:
    """记录一次区域状态迁移。"""
    WORLD_REGION_TRANSITIONS_TOTAL.labels(from_status=from_status, to_status=to_status).inc()
    WORLD_REGION_OPERATIONS_TOTAL.labels(action="status_update").inc()


def set_regions_by_status(status_counts: dict[str, int]) -> None:
    """设置按状态分组的区域数。"""
    for status_label in ("locked", "active", "unstable", "archived"):
        WORLD_REGIONS_BY_STATUS.labels(status=status_label).set(
            status_counts.get(status_label, 0)
        )


def record_npc_create() -> None:
    """记录一次 NPC 创建。"""
    WORLD_NPC_OPERATIONS_TOTAL.labels(action="create").inc()


def set_npcs_by_chapter(chapter_counts: dict[str, int]) -> None:
    """设置按章节分组的 NPC 数。"""
    for chapter_id, count in chapter_counts.items():
        WORLD_NPCS_BY_CHAPTER.labels(chapter_id=chapter_id).set(count)


def record_quest_create() -> None:
    """记录一次 Quest 创建。"""
    WORLD_QUEST_OPERATIONS_TOTAL.labels(action="create").inc()


def set_quests_by_type(type_counts: dict[str, int]) -> None:
    """设置按类型分组的 Quest 数。"""
    for quest_type, count in type_counts.items():
        WORLD_QUESTS_BY_TYPE.labels(quest_type=quest_type).set(count)


WORLD_ITEM_OPERATIONS_TOTAL = Counter(
    "world_item_operations_total",
    "Item 操作次数（按动作类型）",
    labelnames=["action"],
)

WORLD_ITEMS_BY_RARITY = Gauge(
    "world_items_by_rarity",
    "Item 数（按稀有度）",
    labelnames=["rarity"],
)

WORLD_ITEMS_BY_TYPE = Gauge(
    "world_items_by_type",
    "Item 数（按类型）",
    labelnames=["item_type"],
)


def record_item_create() -> None:
    """记录一次 Item 创建。"""
    WORLD_ITEM_OPERATIONS_TOTAL.labels(action="create").inc()


def record_item_update() -> None:
    """记录一次 Item 更新。"""
    WORLD_ITEM_OPERATIONS_TOTAL.labels(action="update").inc()


def record_item_delete() -> None:
    """记录一次 Item 删除。"""
    WORLD_ITEM_OPERATIONS_TOTAL.labels(action="delete").inc()


def set_items_by_rarity(rarity_counts: dict[str, int]) -> None:
    """设置按稀有度分组的 Item 数。"""
    for rarity in ("common", "uncommon", "rare", "epic", "legendary"):
        WORLD_ITEMS_BY_RARITY.labels(rarity=rarity).set(
            rarity_counts.get(rarity, 0)
        )


def set_items_by_type(type_counts: dict[str, int]) -> None:
    """设置按类型分组的 Item 数。"""
    for item_type in ("weapon", "armor", "accessory", "consumable", "material"):
        WORLD_ITEMS_BY_TYPE.labels(item_type=item_type).set(
            type_counts.get(item_type, 0)
        )


WORLD_MONSTER_OPERATIONS_TOTAL = Counter(
    "world_monster_operations_total",
    "Monster 操作次数（按动作类型）",
    labelnames=["action"],
)

WORLD_MONSTERS_BY_TYPE = Gauge(
    "world_monsters_by_type",
    "Monster 数（按怪物类型）",
    labelnames=["monster_type"],
)


def record_monster_create() -> None:
    """记录一次 Monster 创建。"""
    WORLD_MONSTER_OPERATIONS_TOTAL.labels(action="create").inc()


def set_monsters_by_type(type_counts: dict[str, int]) -> None:
    """设置按类型分组的 Monster 数。"""
    for monster_type in ("beast", "humanoid", "undead", "mechanical", "elemental", "demon", "dragon", "boss"):
        WORLD_MONSTERS_BY_TYPE.labels(monster_type=monster_type).set(
            type_counts.get(monster_type, 0)
        )
