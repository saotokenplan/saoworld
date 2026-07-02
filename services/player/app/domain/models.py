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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
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