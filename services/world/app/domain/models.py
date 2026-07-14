import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    UUID,
    CheckConstraint,
    DateTime,
    Index,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Region(Base):
    __tablename__ = "regions"

    region_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chapter_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="locked", server_default="locked", index=True
    )
    visible: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    unlock_condition_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('locked', 'active', 'unstable', 'archived')",
            name="regions_status_check",
        ),
        Index("regions_chapter_id_idx", "chapter_id"),
        Index("regions_status_idx", "status"),
    )


class WorldSkeleton(Base):
    __tablename__ = "world_skeletons"

    skeleton_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    world_version: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    chapter_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    regions: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    factions: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    reserved_characters: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    forbidden_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    reward_limits: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("world_skeletons_is_active_idx", "is_active"),
    )


class NPC(Base):
    __tablename__ = "npcs"

    npc_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    npc_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    chapter_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str | None] = mapped_column(String(128), nullable=True)
    faction_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    location_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    personality: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    dialogues: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    related_quests: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    rewards: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    min_reputation: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0", index=True)
    interaction_restrictions_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "min_reputation >= 0",
            name="npcs_min_reputation_check",
        ),
        Index("npcs_chapter_id_idx", "chapter_id"),
        Index("npcs_faction_key_idx", "faction_key"),
        Index("npcs_min_reputation_idx", "min_reputation"),
    )


class QuestDefinition(Base):
    __tablename__ = "quest_definitions"

    quest_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quest_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    chapter_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quest_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    region_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    start_npc_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    end_npc_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prerequisites: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    objectives: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    rewards: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    failure_condition: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    min_reputation: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0", index=True)
    required_reputation_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "quest_type IN ('main', 'side', 'event', 'daily')",
            name="quest_definitions_quest_type_check",
        ),
        CheckConstraint(
            "min_reputation >= 0",
            name="quest_definitions_min_reputation_check",
        ),
        Index("quest_definitions_chapter_id_idx", "chapter_id"),
        Index("quest_definitions_quest_type_idx", "quest_type"),
        Index("quest_definitions_region_key_idx", "region_key"),
        Index("quest_definitions_min_reputation_idx", "min_reputation"),
    )


class ItemDefinition(Base):
    __tablename__ = "item_definitions"

    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    item_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    item_slot: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rarity: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    chapter_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    level_requirement: Mapped[int] = mapped_column(nullable=False, default=1, server_default="1")
    stats_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    effects_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    sell_price: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    stackable: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    schema_version: Mapped[int] = mapped_column(nullable=False, default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "item_type IN ('weapon', 'armor', 'accessory', 'consumable', 'material')",
            name="item_definitions_item_type_check",
        ),
        CheckConstraint(
            "item_slot IN ('head', 'chest', 'legs', 'feet', 'weapon', 'off_hand', 'ring', 'necklace')",
            name="item_definitions_item_slot_check",
        ),
        CheckConstraint(
            "rarity IN ('common', 'uncommon', 'rare', 'epic', 'legendary')",
            name="item_definitions_rarity_check",
        ),
        CheckConstraint(
            "level_requirement >= 1",
            name="item_definitions_level_requirement_check",
        ),
        CheckConstraint(
            "sell_price >= 0",
            name="item_definitions_sell_price_check",
        ),
        Index("item_definitions_item_type_idx", "item_type"),
        Index("item_definitions_rarity_idx", "rarity"),
        Index("item_definitions_chapter_id_idx", "chapter_id"),
        Index("item_definitions_item_slot_idx", "item_slot"),
    )


class MonsterDefinition(Base):
    __tablename__ = "monster_definitions"

    monster_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    monster_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    monster_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    chapter_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    region_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    level: Mapped[int] = mapped_column(nullable=False, default=1, server_default="1")
    hp: Mapped[int] = mapped_column(nullable=False, default=10)
    attack: Mapped[int] = mapped_column(nullable=False, default=5)
    defense: Mapped[int] = mapped_column(nullable=False, default=0)
    speed: Mapped[int] = mapped_column(nullable=False, default=5)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    behavior_pattern_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    loot_table_jsonb: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    skills_jsonb: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    min_reputation: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0", index=True)
    schema_version: Mapped[int] = mapped_column(nullable=False, default=1, server_default="1")
    is_boss: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false", index=True)
    boss_rank: Mapped[str | None] = mapped_column(String(32), nullable=True)
    phase_count: Mapped[int] = mapped_column(nullable=False, default=1, server_default="1")
    special_skills_jsonb: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    enrage_threshold: Mapped[float] = mapped_column(nullable=False, default=0.0, server_default="0.0")
    reward_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "monster_type IN ('beast', 'humanoid', 'undead', 'mechanical', 'elemental', 'demon', 'dragon', 'boss')",
            name="monster_definitions_monster_type_check",
        ),
        CheckConstraint(
            "level >= 1",
            name="monster_definitions_level_check",
        ),
        CheckConstraint(
            "hp > 0",
            name="monster_definitions_hp_check",
        ),
        CheckConstraint(
            "attack >= 0",
            name="monster_definitions_attack_check",
        ),
        CheckConstraint(
            "defense >= 0",
            name="monster_definitions_defense_check",
        ),
        CheckConstraint(
            "speed >= 0",
            name="monster_definitions_speed_check",
        ),
        CheckConstraint(
            "min_reputation >= 0",
            name="monster_definitions_min_reputation_check",
        ),
        CheckConstraint(
            "boss_rank IN ('legendary', 'mythic')",
            name="monster_definitions_boss_rank_check",
        ),
        CheckConstraint(
            "phase_count >= 1",
            name="monster_definitions_phase_count_check",
        ),
        CheckConstraint(
            "enrage_threshold >= 0 AND enrage_threshold <= 1",
            name="monster_definitions_enrage_threshold_check",
        ),
        Index("monster_definitions_monster_type_idx", "monster_type"),
        Index("monster_definitions_chapter_id_idx", "chapter_id"),
        Index("monster_definitions_region_key_idx", "region_key"),
        Index("monster_definitions_level_idx", "level"),
        Index("monster_definitions_min_reputation_idx", "min_reputation"),
        Index("monster_definitions_is_boss_region_idx", "is_boss", "region_key"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    operator_id: Mapped[str] = mapped_column(String(128), nullable=False)
    operator_role: Mapped[str] = mapped_column(String(16), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_payload_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    result_status: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
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
