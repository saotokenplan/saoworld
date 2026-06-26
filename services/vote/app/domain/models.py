import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    UUID,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class VoteCycle(Base):
    __tablename__ = "vote_cycles"

    vote_cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chapter_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="draft", server_default="draft", index=True
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[str] = mapped_column(String(128), nullable=False)
    created_reason: Mapped[str] = mapped_column(Text, nullable=False)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    winning_candidate_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vote_candidates.candidate_id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    candidates: Mapped[list["VoteCandidate"]] = relationship(back_populates="vote_cycle")

    __table_args__ = (
        CheckConstraint("ends_at &gt; starts_at", name="vote_cycles_ends_after_starts"),
        CheckConstraint(
            "status IN ('draft', 'scheduled', 'open', 'closed', 'finalized')",
            name="vote_cycles_status_check",
        ),
    )


class VoteCandidate(Base):
    __tablename__ = "vote_candidates"

    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vote_cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vote_cycles.vote_cycle_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    region_scope: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="'[]'::jsonb")
    risk_tags: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="'[]'::jsonb")
    generated_params: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="active", server_default="active"
    )
    vote_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    vote_cycle: Mapped["VoteCycle"] = relationship(back_populates="candidates")

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'withdrawn', 'selected')",
            name="vote_candidates_status_check",
        ),
    )


class Vote(Base):
    __tablename__ = "votes"

    vote_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vote_cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vote_cycles.vote_cycle_id"), nullable=False
    )
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vote_candidates.candidate_id"), nullable=False
    )
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0, server_default="1.0")
    device_fingerprint_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("vote_cycle_id", "player_id", name="votes_cycle_player_uniq"),
        CheckConstraint("weight &gt; 0 AND weight &lt;= 10.0", name="votes_weight_range"),
    )
