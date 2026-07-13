import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, UUID, CheckConstraint, DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class OpsDashboard(Base):
    __tablename__ = "ops_dashboards"

    dashboard_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metrics_jsonb: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class OpsAction(Base):
    __tablename__ = "ops_actions"

    action_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    operator_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    operator_role: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed", server_default="completed")
    payload_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    __table_args__ = (
        CheckConstraint(
            "action_type IN ('vote_cycle_create', 'vote_cycle_transition', 'content_release', "
            "'content_rollback', 'review_approve', 'player_create', 'region_unlock', 'dashboard_view')",
            name="ops_actions_action_type_check",
        ),
        CheckConstraint(
            "operator_role IN ('player', 'ops', 'reviewer', 'system')",
            name="ops_actions_operator_role_check",
        ),
        CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name="ops_actions_status_check",
        ),
        Index("ops_actions_resource_idx", "resource_type", "resource_id"),
        Index("ops_actions_action_idx", "action_type", "created_at"),
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


class PlayerEvent(Base):
    __tablename__ = "player_events"

    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    player_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    region_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    payload_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    producer: Mapped[str] = mapped_column(String(64), nullable=False, default="gateway")
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("player_events_player_idx", "player_id", "occurred_at"),
        Index("player_events_region_idx", "region_id", "occurred_at"),
        Index("player_events_type_idx", "event_type", "occurred_at"),
    )


class PlayerMetricsDaily(Base):
    __tablename__ = "player_metrics_daily"

    metric_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[str] = mapped_column(String(128), nullable=False)
    stat_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_session_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    regions_visited: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quests_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    votes_submitted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    npcs_interacted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    events_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    detail_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("player_metrics_daily_player_date_idx", "player_id", "stat_date", unique=True),
    )


class RegionMetricsDaily(Base):
    __tablename__ = "region_metrics_daily"

    metric_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region_id: Mapped[str] = mapped_column(String(128), nullable=False)
    stat_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    unique_players: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_visits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quests_started: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quests_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    events_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    detail_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("region_metrics_daily_region_date_idx", "region_id", "stat_date", unique=True),
    )


class QuestMetricsDaily(Base):
    __tablename__ = "quest_metrics_daily"

    metric_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quest_id: Mapped[str] = mapped_column(String(128), nullable=False)
    stat_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    events_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    detail_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("quest_metrics_daily_quest_date_idx", "quest_id", "stat_date", unique=True),
    )


class VoteMetricsDaily(Base):
    __tablename__ = "vote_metrics_daily"

    metric_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vote_cycle_id: Mapped[str] = mapped_column(String(128), nullable=False)
    stat_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_votes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unique_voters: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    candidate_votes_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    events_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    detail_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("vote_metrics_daily_cycle_date_idx", "vote_cycle_id", "stat_date", unique=True),
    )


class AnalyticsReport(Base):
    __tablename__ = "analytics_reports"

    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", server_default="pending")
    summary_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    detail_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    generated_by: Mapped[str] = mapped_column(String(64), nullable=False, default="system")
    trace_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "report_type IN ('daily_summary', 'weekly_summary', 'monthly_summary', "
            "'player_behavior', 'region_heatmap', 'quest_performance', 'vote_analysis', 'custom')",
            name="analytics_reports_type_check",
        ),
        CheckConstraint(
            "status IN ('pending', 'generating', 'completed', 'failed')",
            name="analytics_reports_status_check",
        ),
        Index("analytics_reports_period_idx", "report_type", "period_start", "period_end"),
    )


class Insight(Base):
    __tablename__ = "insights"

    insight_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    impact: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    novelty: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    feasibility: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    quality_score: Mapped[float] = mapped_column(nullable=False, default=0.0)
    source_report_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    source_data_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "category IN ('content_preference', 'region_heat', 'vote_preference', "
            "'difficulty_feedback', 'content_gap', 'player_behavior', 'system_health')",
            name="insights_category_check",
        ),
        CheckConstraint(
            "confidence IN ('low', 'medium', 'high')",
            name="insights_confidence_check",
        ),
        CheckConstraint(
            "impact IN ('low', 'medium', 'high')",
            name="insights_impact_check",
        ),
        CheckConstraint(
            "novelty IN ('low', 'medium', 'high')",
            name="insights_novelty_check",
        ),
        CheckConstraint(
            "feasibility IN ('low', 'medium', 'high')",
            name="insights_feasibility_check",
        ),
        Index("insights_category_idx", "category"),
        Index("insights_score_idx", "quality_score"),
        Index("insights_discovered_at_idx", "discovered_at"),
    )


class Requirement(Base):
    __tablename__ = "requirements"

    requirement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    insight_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending_review", server_default="pending_review"
    )
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    target_scope: Mapped[str] = mapped_column(String(64), nullable=False, default="content")
    estimated_effort: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    acceptance_criteria_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    related_content_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    generated_by: Mapped[str] = mapped_column(String(64), nullable=False, default="system")
    approved_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending_review', 'approved', 'rejected', 'in_progress', 'completed')",
            name="requirements_status_check",
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'critical')",
            name="requirements_priority_check",
        ),
        CheckConstraint(
            "target_scope IN ('content', 'gameplay', 'system', 'world')",
            name="requirements_scope_check",
        ),
        Index("requirements_insight_idx", "insight_id"),
        Index("requirements_status_idx", "status"),
        Index("requirements_priority_idx", "priority"),
    )
