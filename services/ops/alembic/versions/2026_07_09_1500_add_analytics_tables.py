"""add analytics tables

Revision ID: 2026_07_09_1500
Revises: 2026_07_09_1400
Create Date: 2026-07-09 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2026_07_09_1500'
down_revision: Union[str, Sequence[str], None] = '2026_07_09_1400'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "player_metrics_daily",
        sa.Column("metric_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("player_id", sa.String(length=128), nullable=False),
        sa.Column("stat_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_session_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("regions_visited", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quests_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("votes_submitted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("npcs_interacted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("events_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("detail_jsonb", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "player_metrics_daily_player_date_idx",
        "player_metrics_daily",
        ["player_id", "stat_date"],
        unique=True,
    )

    op.create_table(
        "region_metrics_daily",
        sa.Column("metric_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("region_id", sa.String(length=128), nullable=False),
        sa.Column("stat_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("unique_players", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_visits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quests_started", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quests_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("events_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("detail_jsonb", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "region_metrics_daily_region_date_idx",
        "region_metrics_daily",
        ["region_id", "stat_date"],
        unique=True,
    )

    op.create_table(
        "quest_metrics_daily",
        sa.Column("metric_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("quest_id", sa.String(length=128), nullable=False),
        sa.Column("stat_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("events_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("detail_jsonb", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "quest_metrics_daily_quest_date_idx",
        "quest_metrics_daily",
        ["quest_id", "stat_date"],
        unique=True,
    )

    op.create_table(
        "vote_metrics_daily",
        sa.Column("metric_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("vote_cycle_id", sa.String(length=128), nullable=False),
        sa.Column("stat_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_votes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unique_voters", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("candidate_votes_jsonb", sa.JSON(), nullable=True),
        sa.Column("events_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("detail_jsonb", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "vote_metrics_daily_cycle_date_idx",
        "vote_metrics_daily",
        ["vote_cycle_id", "stat_date"],
        unique=True,
    )

    op.create_table(
        "analytics_reports",
        sa.Column("report_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("report_type", sa.String(length=64), nullable=False, index=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("summary_jsonb", sa.JSON(), nullable=True),
        sa.Column("detail_jsonb", sa.JSON(), nullable=True),
        sa.Column("generated_by", sa.String(length=64), nullable=False, server_default="system"),
        sa.Column("trace_id", sa.String(length=128), nullable=True),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_check_constraint(
        "analytics_reports_type_check",
        "analytics_reports",
        "report_type IN ('daily_summary', 'weekly_summary', 'monthly_summary', "
        "'player_behavior', 'region_heatmap', 'quest_performance', 'vote_analysis', 'custom')",
    )
    op.create_check_constraint(
        "analytics_reports_status_check",
        "analytics_reports",
        "status IN ('pending', 'generating', 'completed', 'failed')",
    )
    op.create_index(
        "analytics_reports_period_idx",
        "analytics_reports",
        ["report_type", "period_start", "period_end"],
    )


def downgrade() -> None:
    op.drop_index("analytics_reports_period_idx", table_name="analytics_reports")
    op.drop_constraint("analytics_reports_status_check", table_name="analytics_reports", type_="check")
    op.drop_constraint("analytics_reports_type_check", table_name="analytics_reports", type_="check")
    op.drop_table("analytics_reports")

    op.drop_index("vote_metrics_daily_cycle_date_idx", table_name="vote_metrics_daily")
    op.drop_table("vote_metrics_daily")

    op.drop_index("quest_metrics_daily_quest_date_idx", table_name="quest_metrics_daily")
    op.drop_table("quest_metrics_daily")

    op.drop_index("region_metrics_daily_region_date_idx", table_name="region_metrics_daily")
    op.drop_table("region_metrics_daily")

    op.drop_index("player_metrics_daily_player_date_idx", table_name="player_metrics_daily")
    op.drop_table("player_metrics_daily")
