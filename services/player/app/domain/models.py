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
