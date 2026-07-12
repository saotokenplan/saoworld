import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    UUID,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


def _default_json_list():
    return []


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
        UUID(as_uuid=True),
        ForeignKey("vote_candidates.candidate_id", use_alter=True, name="fk_vote_cycles_winning_candidate"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    candidates: Mapped[list["VoteCandidate"]] = relationship(
        back_populates="vote_cycle",
        foreign_keys="VoteCandidate.vote_cycle_id",
    )

    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="vote_cycles_ends_after_starts"),
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
    region_scope: Mapped[list] = mapped_column(JSON, nullable=False, default=_default_json_list)
    risk_tags: Mapped[list] = mapped_column(JSON, nullable=False, default=_default_json_list)
    generated_params: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
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

    vote_cycle: Mapped["VoteCycle"] = relationship(
        back_populates="candidates",
        foreign_keys=[vote_cycle_id],
    )

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
        CheckConstraint("weight > 0 AND weight <= 10.0", name="votes_weight_range"),
        Index("votes_candidate_id_idx", "candidate_id"),
    )


class VoteDiscussion(Base):
    __tablename__ = "vote_discussions"

    discussion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vote_cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vote_cycles.vote_cycle_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    reply_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="active", server_default="active", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    replies: Mapped[list["VoteDiscussionReply"]] = relationship(
        back_populates="discussion",
        foreign_keys="VoteDiscussionReply.discussion_id",
    )

    __table_args__ = (
        CheckConstraint("length(content) >= 1 AND length(content) <= 500", name="discussions_content_length"),
        CheckConstraint(
            "status IN ('active', 'hidden', 'deleted')",
            name="discussions_status_check",
        ),
        Index("vote_discussions_cycle_created_idx", "vote_cycle_id", "created_at"),
        Index("vote_discussions_cycle_likes_idx", "vote_cycle_id", "like_count"),
    )


class VoteDiscussionReply(Base):
    __tablename__ = "vote_discussion_replies"

    reply_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    discussion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vote_discussions.discussion_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="active", server_default="active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    discussion: Mapped["VoteDiscussion"] = relationship(
        back_populates="replies",
        foreign_keys=[discussion_id],
    )

    __table_args__ = (
        CheckConstraint("length(content) >= 1 AND length(content) <= 500", name="replies_content_length"),
        CheckConstraint(
            "status IN ('active', 'hidden', 'deleted')",
            name="replies_status_check",
        ),
        Index("vote_discussion_replies_discussion_created_idx", "discussion_id", "created_at"),
    )


class VoteDiscussionLike(Base):
    __tablename__ = "vote_discussion_likes"

    like_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    discussion_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vote_discussions.discussion_id", ondelete="CASCADE"),
        nullable=True,
    )
    reply_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vote_discussion_replies.reply_id", ondelete="CASCADE"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "player_id", "discussion_id",
            name="vote_discussion_likes_player_discussion_uniq",
        ),
        UniqueConstraint(
            "player_id", "reply_id",
            name="vote_discussion_likes_player_reply_uniq",
        ),
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
