import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.domain.uuid_type import UUIDType


class Player(Base):
    __tablename__ = "players"

    player_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    reputation_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    progress_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    chapter_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contribution_points: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    level: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    experience_points: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "contribution_points >= 0", name="players_contribution_points_check"
        ),
        CheckConstraint(
            "level >= 1", name="players_level_check"
        ),
        CheckConstraint(
            "experience_points >= 0", name="players_experience_points_check"
        ),
    )


class PlayerContribution(Base):
    __tablename__ = "player_contributions"

    contribution_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    player_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="player_contributions_amount_check"),
        CheckConstraint(
            "source IN ('quest', 'vote', 'building', 'ops', 'system')",
            name="player_contributions_source_check",
        ),
        Index("player_contributions_player_created_idx", "player_id", "created_at"),
    )


class AchievementDefinition(Base):
    __tablename__ = "achievement_definitions"

    achievement_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(256), nullable=True)
    rarity: Mapped[str] = mapped_column(String(32), nullable=False, server_default="common")
    category: Mapped[str] = mapped_column(String(32), nullable=False, server_default="quest")
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=10, server_default="10")
    reward_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    condition_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "rarity IN ('common', 'uncommon', 'rare', 'epic', 'legendary')",
            name="achievement_definitions_rarity_check",
        ),
        CheckConstraint(
            "category IN ('quest', 'exploration', 'combat', 'reputation', 'vote', 'social', 'collection')",
            name="achievement_definitions_category_check",
        ),
        CheckConstraint("points >= 0", name="achievement_definitions_points_check"),
        Index("achievement_definitions_category_idx", "category"),
        Index("achievement_definitions_rarity_idx", "rarity"),
        Index("achievement_definitions_is_active_idx", "is_active"),
    )


class PlayerAchievement(Base):
    __tablename__ = "player_achievements"

    player_achievement_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    player_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    achievement_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    reward_claimed: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, server_default="system")
    source_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "source IN ('quest', 'exploration', 'combat', 'reputation', 'vote', 'ops', 'system')",
            name="player_achievements_source_check",
        ),
        Index("player_achievements_player_achievement_idx", "player_id", "achievement_key", unique=True),
        Index("player_achievements_player_unlocked_idx", "player_id", "unlocked_at"),
    )


class PlayerQuest(Base):
    __tablename__ = "player_quests"

    player_quest_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    quest_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="available", server_default="available", index=True
    )
    objectives_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    rewards_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('available', 'active', 'completed', 'failed')",
            name="player_quests_status_check",
        ),
        Index("player_quests_player_quest_idx", "player_id", "quest_id"),
    )


class PlayerInventory(Base):
    __tablename__ = "player_inventories"

    inventory_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    item_key: Mapped[str] = mapped_column(String(128), nullable=False)
    item_type: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="material"
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    metadata_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "item_type IN ('consumable', 'equipment', 'material', 'quest_item')",
            name="player_inventories_item_type_check",
        ),
        CheckConstraint(
            "quantity > 0",
            name="player_inventories_quantity_check",
        ),
        Index("player_inventories_player_item_idx", "player_id", "item_key", unique=True),
    )


class PlayerEquipment(Base):
    __tablename__ = "player_equipment"

    equipment_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    slot: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    item_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    item_instance_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, default=uuid.uuid4)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    stats_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    equipped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "slot IN ('head', 'chest', 'legs', 'feet', 'weapon', 'off_hand', 'ring', 'necklace')",
            name="player_equipment_slot_check",
        ),
        CheckConstraint(
            "level >= 0",
            name="player_equipment_level_check",
        ),
        Index("player_equipment_player_slot_idx", "player_id", "slot", unique=True),
        Index("player_equipment_item_key_idx", "item_key"),
    )


class PlayerRegion(Base):
    __tablename__ = "player_regions"

    player_region_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    region_id: Mapped[str] = mapped_column(String(128), nullable=False)
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reputation: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("player_regions_player_region_idx", "player_id", "region_id"),
    )


class Friendship(Base):
    __tablename__ = "friendships"

    friendship_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), nullable=False, index=True,
    )
    friend_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), nullable=False, index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", server_default="pending", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'accepted', 'rejected', 'blocked')",
            name="friendships_status_check",
        ),
        Index("friendships_player_friend_idx", "player_id", "friend_id", unique=True),
        Index("friendships_friend_status_idx", "friend_id", "status"),
    )


class PrivateMessage(Base):
    """私聊消息表。"""

    __tablename__ = "private_messages"

    message_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    sender_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    receiver_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "length(content) > 0 AND length(content) <= 500",
            name="private_messages_content_check",
        ),
        Index("private_messages_sender_created_idx", "sender_id", "created_at"),
        Index("private_messages_receiver_created_idx", "receiver_id", "created_at"),
        Index("private_messages_conversation_idx", "sender_id", "receiver_id"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    trace_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    operator_id: Mapped[str] = mapped_column(String(128), nullable=False)
    operator_role: Mapped[str] = mapped_column(String(16), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType(), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_payload_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    result_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "operator_role IN ('player', 'ops', 'reviewer', 'system')",
            name="audit_logs_operator_role_check",
        ),
        Index("audit_logs_operator_id_idx", "operator_id", "created_at"),
        Index("audit_logs_resource_idx", "resource_type", "resource_id"),
        Index("audit_logs_action_idx", "action", "created_at"),
    )


class Guild(Base):
    """公会表。"""

    __tablename__ = "guilds"

    guild_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    leader_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    announcement: Mapped[str | None] = mapped_column(Text, nullable=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    member_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    max_members: Mapped[int] = mapped_column(Integer, nullable=False, default=50, server_default="50")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "length(name) > 0 AND length(name) <= 64",
            name="guilds_name_check",
        ),
        CheckConstraint(
            "level >= 1",
            name="guilds_level_check",
        ),
        CheckConstraint(
            "member_count >= 1",
            name="guilds_member_count_check",
        ),
        CheckConstraint(
            "max_members >= 1",
            name="guilds_max_members_check",
        ),
        CheckConstraint(
            "member_count <= max_members",
            name="guilds_capacity_check",
        ),
    )


class GuildMember(Base):
    """公会成员表。"""

    __tablename__ = "guild_members"

    guild_member_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    player_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(
        String(16), nullable=False, default="member", server_default="member", index=True
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('leader', 'officer', 'member')",
            name="guild_members_role_check",
        ),
        Index("guild_members_guild_joined_idx", "guild_id", "joined_at"),
    )


class GuildMessage(Base):
    """公会消息表。"""

    __tablename__ = "guild_messages"

    message_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    sender_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "length(content) > 0 AND length(content) <= 500",
            name="guild_messages_content_check",
        ),
        Index("guild_messages_guild_created_idx", "guild_id", "created_at"),
        Index("guild_messages_sender_created_idx", "sender_id", "created_at"),
    )


class GuildQuest(Base):
    """公会任务表。"""

    __tablename__ = "guild_quests"

    guild_quest_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    quest_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quest_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="collect", server_default="collect", index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="active", server_default="active", index=True
    )
    objectives_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    rewards_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    progress_target: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    current_progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    time_limit_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=1440, server_default="1440")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "quest_type IN ('collect', 'kill', 'deliver', 'explore', 'defend', 'craft')",
            name="guild_quests_type_check",
        ),
        CheckConstraint(
            "status IN ('active', 'completed', 'failed', 'expired')",
            name="guild_quests_status_check",
        ),
        CheckConstraint("progress_target > 0", name="guild_quests_target_check"),
        CheckConstraint("current_progress >= 0", name="guild_quests_progress_check"),
        CheckConstraint("time_limit_minutes > 0", name="guild_quests_time_check"),
        Index("guild_quests_guild_status_idx", "guild_id", "status"),
        Index("guild_quests_guild_key_idx", "guild_id", "quest_key", unique=True),
    )


class GuildQuestProgress(Base):
    """公会成员任务进度表。"""

    __tablename__ = "guild_quest_progress"

    progress_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    guild_quest_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    player_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    contribution: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    claimed_reward: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("contribution >= 0", name="guild_quest_progress_contribution_check"),
        Index("guild_quest_progress_player_idx", "player_id", "guild_quest_id", unique=True),
        Index("guild_quest_progress_quest_idx", "guild_quest_id", "created_at"),
    )


class PlayerTrade(Base):
    """玩家交易记录表。"""

    __tablename__ = "player_trades"

    trade_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    initiator_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    recipient_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", server_default="pending", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'accepted', 'rejected', 'cancelled', 'completed')",
            name="player_trades_status_check",
        ),
        Index("player_trades_initiator_status_idx", "initiator_id", "status"),
        Index("player_trades_recipient_status_idx", "recipient_id", "status"),
    )


class TradeItem(Base):
    """交易物品明细表。"""

    __tablename__ = "trade_items"

    trade_item_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    trade_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    from_player_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    item_key: Mapped[str] = mapped_column(String(128), nullable=False)
    item_type: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="material"
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    __table_args__ = (
        CheckConstraint(
            "item_type IN ('consumable', 'equipment', 'material', 'quest_item')",
            name="trade_items_item_type_check",
        ),
        CheckConstraint("quantity > 0", name="trade_items_quantity_check"),
        Index("trade_items_trade_idx", "trade_id"),
    )


class TradeCoin(Base):
    """交易金币明细表。"""

    __tablename__ = "trade_coins"

    trade_coin_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    trade_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    from_player_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("amount > 0", name="trade_coins_amount_check"),
        Index("trade_coins_trade_idx", "trade_id"),
    )


class AuctionListing(Base):
    """拍卖行挂单表。"""

    __tablename__ = "auction_listings"

    listing_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    seller_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    item_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    item_type: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="material"
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    starting_price: Mapped[int] = mapped_column(Integer, nullable=False)
    current_price: Mapped[int] = mapped_column(Integer, nullable=False)
    buyout_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="active", server_default="active", index=True
    )
    highest_bidder_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sold_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    buyer_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType(), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "item_type IN ('consumable', 'equipment', 'material', 'quest_item')",
            name="auction_listings_item_type_check",
        ),
        CheckConstraint("quantity > 0", name="auction_listings_quantity_check"),
        CheckConstraint("starting_price >= 0", name="auction_listings_starting_price_check"),
        CheckConstraint("current_price >= 0", name="auction_listings_current_price_check"),
        CheckConstraint(
            "status IN ('active', 'sold', 'expired', 'cancelled')",
            name="auction_listings_status_check",
        ),
        Index("auction_listings_seller_status_idx", "seller_id", "status"),
        Index("auction_listings_item_key_idx", "item_key", "status"),
        Index("auction_listings_expires_idx", "expires_at"),
    )


class GuildWar(Base):
    """公会战表。"""

    __tablename__ = "guild_wars"

    war_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    challenger_guild_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    defender_guild_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="declared", server_default="declared", index=True
    )
    war_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="territory", server_default="territory", index=True
    )
    declared_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    winner_guild_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType(), nullable=True, index=True)
    challenger_score: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    defender_score: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    reward_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('declared', 'accepted', 'in_progress', 'completed', 'cancelled')",
            name="guild_wars_status_check",
        ),
        CheckConstraint(
            "war_type IN ('territory', 'resource', 'honor')",
            name="guild_wars_type_check",
        ),
        CheckConstraint("challenger_score >= 0", name="guild_wars_challenger_score_check"),
        CheckConstraint("defender_score >= 0", name="guild_wars_defender_score_check"),
        Index("guild_wars_challenger_status_idx", "challenger_guild_id", "status"),
        Index("guild_wars_defender_status_idx", "defender_guild_id", "status"),
    )


class GuildWarParticipant(Base):
    """公会战参与成员表。"""

    __tablename__ = "guild_war_participants"

    participant_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    war_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    guild_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    player_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    kills: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    deaths: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    contribution_score: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("kills >= 0", name="guild_war_participants_kills_check"),
        CheckConstraint("deaths >= 0", name="guild_war_participants_deaths_check"),
        CheckConstraint("contribution_score >= 0", name="guild_war_participants_contribution_check"),
        Index("guild_war_participants_war_player_idx", "war_id", "player_id", unique=True),
        Index("guild_war_participants_war_guild_idx", "war_id", "guild_id"),
    )


class FriendCollabQuest(Base):
    """好友协作任务表。"""

    __tablename__ = "friend_collab_quests"

    quest_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    initiator_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    friend_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    quest_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="hunt", server_default="hunt", index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending_invite", server_default="pending_invite", index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    objectives_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    progress_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    rewards_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    schema_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "quest_type IN ('hunt', 'explore', 'collect', 'escort', 'challenge')",
            name="friend_collab_quests_type_check",
        ),
        CheckConstraint(
            "status IN ('pending_invite', 'active', 'completed', 'failed', 'expired')",
            name="friend_collab_quests_status_check",
        ),
        Index("friend_collab_quests_initiator_status_idx", "initiator_id", "status"),
        Index("friend_collab_quests_friend_status_idx", "friend_id", "status"),
    )


class PlayerWallet(Base):
    """玩家钱包表。"""

    __tablename__ = "player_wallets"

    wallet_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, unique=True, index=True)
    gold_coins: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("gold_coins >= 0", name="player_wallets_gold_check"),
    )


class WalletTransaction(Base):
    """钱包流水表。"""

    __tablename__ = "wallet_transactions"

    transaction_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    wallet_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    player_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    transaction_type: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_before: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "transaction_type IN ('earn', 'spend', 'trade_send', 'trade_receive', "
            "'auction_sell', 'auction_buy', 'fee', 'tax', 'gift', 'quest_reward')",
            name="wallet_transactions_type_check",
        ),
        Index("wallet_transactions_player_idx", "player_id", "created_at"),
        Index("wallet_transactions_wallet_idx", "wallet_id", "created_at"),
    )


class MatchSeason(Base):
    """匹配赛季表。"""

    __tablename__ = "match_seasons"

    season_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    season_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    season_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="upcoming", server_default="upcoming", index=True
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reward_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    schema_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('upcoming', 'active', 'ended', 'archived')",
            name="match_seasons_status_check",
        ),
        Index("match_seasons_status_idx", "status"),
        Index("match_seasons_time_idx", "start_at", "end_at"),
    )


class PlayerRating(Base):
    """玩家段位表。"""

    __tablename__ = "player_ratings"

    rating_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    season_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    tier: Mapped[str] = mapped_column(
        String(32), nullable=False, default="bronze", server_default="bronze", index=True
    )
    division: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5, server_default="5"
    )
    rating_points: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    wins: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    losses: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    draws: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    win_streak: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    best_tier: Mapped[str] = mapped_column(
        String(32), nullable=False, default="bronze", server_default="bronze"
    )
    best_division: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5, server_default="5"
    )
    schema_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "tier IN ('bronze', 'silver', 'gold', 'platinum', 'diamond', 'master', 'challenger')",
            name="player_ratings_tier_check",
        ),
        CheckConstraint("division >= 1 AND division <= 5", name="player_ratings_division_check"),
        CheckConstraint("rating_points >= 0", name="player_ratings_points_check"),
        CheckConstraint("wins >= 0", name="player_ratings_wins_check"),
        CheckConstraint("losses >= 0", name="player_ratings_losses_check"),
        CheckConstraint("draws >= 0", name="player_ratings_draws_check"),
        CheckConstraint("win_streak >= 0", name="player_ratings_win_streak_check"),
        Index("player_ratings_player_season_idx", "player_id", "season_id", unique=True),
        Index("player_ratings_season_tier_idx", "season_id", "tier"),
    )


class MatchQueue(Base):
    """匹配队列表。"""

    __tablename__ = "match_queues"

    queue_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    season_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    match_mode: Mapped[str] = mapped_column(
        String(32), nullable=False, default="solo_1v1", server_default="solo_1v1", index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="queuing", server_default="queuing", index=True
    )
    tier: Mapped[str] = mapped_column(
        String(32), nullable=False, default="bronze", server_default="bronze"
    )
    division: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5, server_default="5"
    )
    player_level: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    matched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    match_room_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType(), nullable=True, index=True)
    timeout_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    schema_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('queuing', 'matched', 'cancelled', 'timeout')",
            name="match_queues_status_check",
        ),
        CheckConstraint(
            "match_mode IN ('solo_1v1', 'team_2v2', 'team_3v3')",
            name="match_queues_mode_check",
        ),
        CheckConstraint(
            "tier IN ('bronze', 'silver', 'gold', 'platinum', 'diamond', 'master', 'challenger')",
            name="match_queues_tier_check",
        ),
        CheckConstraint("division >= 1 AND division <= 5", name="match_queues_division_check"),
        CheckConstraint("player_level >= 1", name="match_queues_level_check"),
        Index("match_queues_player_status_idx", "player_id", "status"),
        Index("match_queues_mode_status_idx", "match_mode", "status"),
        Index("match_queues_joined_idx", "joined_at"),
    )


class MatchRoom(Base):
    """对战房间表。"""

    __tablename__ = "match_rooms"

    room_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    season_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    match_mode: Mapped[str] = mapped_column(
        String(32), nullable=False, default="solo_1v1", server_default="solo_1v1", index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="waiting", server_default="waiting", index=True
    )
    player1_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    player2_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    player1_ready: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default="false"
    )
    player2_ready: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default="false"
    )
    winner_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType(), nullable=True, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    match_data_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    schema_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('waiting', 'ready', 'in_progress', 'completed', 'cancelled')",
            name="match_rooms_status_check",
        ),
        CheckConstraint(
            "match_mode IN ('solo_1v1', 'team_2v2', 'team_3v3')",
            name="match_rooms_mode_check",
        ),
        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds >= 0",
            name="match_rooms_duration_check",
        ),
        Index("match_rooms_season_status_idx", "season_id", "status"),
        Index("match_rooms_player1_idx", "player1_id", "created_at"),
        Index("match_rooms_player2_idx", "player2_id", "created_at"),
    )


class MatchResult(Base):
    """对战结果表。"""

    __tablename__ = "match_results"

    result_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, unique=True)
    season_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    match_mode: Mapped[str] = mapped_column(
        String(32), nullable=False, default="solo_1v1", server_default="solo_1v1", index=True
    )
    winner_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType(), nullable=True, index=True)
    loser_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType(), nullable=True, index=True)
    is_draw: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default="false"
    )
    winner_rating_change: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    loser_rating_change: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    winner_tier_before: Mapped[str] = mapped_column(String(32), nullable=False)
    winner_division_before: Mapped[int] = mapped_column(Integer, nullable=False)
    winner_tier_after: Mapped[str] = mapped_column(String(32), nullable=False)
    winner_division_after: Mapped[int] = mapped_column(Integer, nullable=False)
    loser_tier_before: Mapped[str] = mapped_column(String(32), nullable=False)
    loser_division_before: Mapped[int] = mapped_column(Integer, nullable=False)
    loser_tier_after: Mapped[str] = mapped_column(String(32), nullable=False)
    loser_division_after: Mapped[int] = mapped_column(Integer, nullable=False)
    match_data_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    submitted_by: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False)
    schema_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "match_mode IN ('solo_1v1', 'team_2v2', 'team_3v3')",
            name="match_results_mode_check",
        ),
        Index("match_results_season_idx", "season_id", "created_at"),
        Index("match_results_winner_idx", "winner_id", "created_at"),
        Index("match_results_loser_idx", "loser_id", "created_at"),
    )
