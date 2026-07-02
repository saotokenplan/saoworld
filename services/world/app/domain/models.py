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
