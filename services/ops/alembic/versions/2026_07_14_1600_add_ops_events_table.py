"""add ops_events table

Revision ID: 2026_07_14_1600
Revises: 2026_07_09_1700
Create Date: 2026-07-14 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2026_07_14_1600'
down_revision: Union[str, Sequence[str], None] = '2026_07_09_1700'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ops_events",
        sa.Column("event_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("event_name", sa.String(length=256), nullable=False, unique=True),
        sa.Column("event_type", sa.String(length=32), nullable=False, index=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft", index=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("target_scope", sa.String(length=32), nullable=False, server_default="all"),
        sa.Column("target_scope_jsonb", sa.JSON(), nullable=True),
        sa.Column("reward_config_jsonb", sa.JSON(), nullable=True),
        sa.Column("multiplier_config_jsonb", sa.JSON(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("rules_jsonb", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.String(length=128), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_check_constraint(
        "ops_events_event_type_check",
        "ops_events",
        "event_type IN ('double_reward', 'login_bonus', 'limited_time', 'sale', 'custom')",
    )
    op.create_check_constraint(
        "ops_events_status_check",
        "ops_events",
        "status IN ('draft', 'active', 'paused', 'ended', 'archived')",
    )
    op.create_check_constraint(
        "ops_events_target_scope_check",
        "ops_events",
        "target_scope IN ('all', 'region', 'player_level', 'guild')",
    )

    op.create_index("ops_events_status_time_idx", "ops_events", ["status", "start_at", "end_at"])
    op.create_index("ops_events_type_idx", "ops_events", ["event_type"])
    op.create_index("ix_ops_events_event_name", "ops_events", ["event_name"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_ops_events_event_name", table_name="ops_events")
    op.drop_index("ops_events_type_idx", table_name="ops_events")
    op.drop_index("ops_events_status_time_idx", table_name="ops_events")
    op.drop_constraint("ops_events_target_scope_check", "ops_events", type_="check")
    op.drop_constraint("ops_events_status_check", "ops_events", type_="check")
    op.drop_constraint("ops_events_event_type_check", "ops_events", type_="check")
    op.drop_table("ops_events")
