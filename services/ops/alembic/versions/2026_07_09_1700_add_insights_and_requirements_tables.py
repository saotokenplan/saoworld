"""Add insights and requirements tables

Revision ID: 2026_07_09_1700_add_insights_and_requirements_tables
Revises: 2026_07_09_1500_add_analytics_tables
Create Date: 2026-07-09 17:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026_07_09_1700_add_insights_and_requirements_tables"
down_revision = "2026_07_09_1500_add_analytics_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "insights",
        sa.Column("insight_id", sa.UUID(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("confidence", sa.String(length=16), nullable=False, server_default="medium"),
        sa.Column("impact", sa.String(length=16), nullable=False, server_default="medium"),
        sa.Column("novelty", sa.String(length=16), nullable=False, server_default="medium"),
        sa.Column("feasibility", sa.String(length=16), nullable=False, server_default="medium"),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("source_report_id", sa.UUID(), nullable=True),
        sa.Column("source_data_jsonb", sa.JSON(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("insight_id"),
        sa.CheckConstraint(
            "category IN ('content_preference', 'region_heat', 'vote_preference', "
            "'difficulty_feedback', 'content_gap', 'player_behavior', 'system_health')",
            name="insights_category_check",
        ),
        sa.CheckConstraint("confidence IN ('low', 'medium', 'high')", name="insights_confidence_check"),
        sa.CheckConstraint("impact IN ('low', 'medium', 'high')", name="insights_impact_check"),
        sa.CheckConstraint("novelty IN ('low', 'medium', 'high')", name="insights_novelty_check"),
        sa.CheckConstraint("feasibility IN ('low', 'medium', 'high')", name="insights_feasibility_check"),
    )
    op.create_index("insights_category_idx", "insights", ["category"])
    op.create_index("insights_score_idx", "insights", ["quality_score"])
    op.create_index("insights_discovered_at_idx", "insights", ["discovered_at"])

    op.create_table(
        "requirements",
        sa.Column("requirement_id", sa.UUID(), nullable=False),
        sa.Column("insight_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending_review"),
        sa.Column("priority", sa.String(length=16), nullable=False, server_default="medium"),
        sa.Column("target_scope", sa.String(length=64), nullable=False, server_default="content"),
        sa.Column("estimated_effort", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("acceptance_criteria_jsonb", sa.JSON(), nullable=True),
        sa.Column("related_content_jsonb", sa.JSON(), nullable=True),
        sa.Column("generated_by", sa.String(length=64), nullable=False, server_default="system"),
        sa.Column("approved_by", sa.String(length=128), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trace_id", sa.String(length=128), nullable=True),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"), index=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("requirement_id"),
        sa.CheckConstraint(
            "status IN ('pending_review', 'approved', 'rejected', 'in_progress', 'completed')",
            name="requirements_status_check",
        ),
        sa.CheckConstraint("priority IN ('low', 'medium', 'high', 'critical')", name="requirements_priority_check"),
        sa.CheckConstraint("target_scope IN ('content', 'gameplay', 'system', 'world')", name="requirements_scope_check"),
    )
    op.create_index("requirements_insight_idx", "requirements", ["insight_id"])
    op.create_index("requirements_status_idx", "requirements", ["status"])
    op.create_index("requirements_priority_idx", "requirements", ["priority"])


def downgrade() -> None:
    op.drop_table("requirements")
    op.drop_table("insights")