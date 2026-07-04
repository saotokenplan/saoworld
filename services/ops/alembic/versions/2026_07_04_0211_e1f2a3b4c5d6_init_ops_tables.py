"""init ops tables

Revision ID: e1f2a3b4c5d6
Revises: 
Create Date: 2026-07-04 02:11:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "ops_dashboards",
        sa.Column("dashboard_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("metrics_jsonb", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ops_dashboards_generated_at_idx", "ops_dashboards", ["generated_at"])

    op.create_table(
        "ops_actions",
        sa.Column("action_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("operator_id", sa.String(length=128), nullable=False),
        sa.Column("operator_role", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"),
        sa.Column("payload_jsonb", sa.JSON(), nullable=True),
        sa.Column("trace_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "action_type IN ('vote_cycle_create', 'vote_cycle_transition', 'content_release', "
            "'content_rollback', 'review_approve', 'player_create', 'region_unlock', 'dashboard_view')",
            name="ops_actions_action_type_check",
        ),
        sa.CheckConstraint(
            "operator_role IN ('player', 'ops', 'reviewer', 'system')",
            name="ops_actions_operator_role_check",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name="ops_actions_status_check",
        ),
    )
    op.create_index("ops_actions_action_type_idx", "ops_actions", ["action_type"])
    op.create_index("ops_actions_operator_id_idx", "ops_actions", ["operator_id"])
    op.create_index("ops_actions_created_at_idx", "ops_actions", ["created_at"])
    op.create_index("ops_actions_resource_idx", "ops_actions", ["resource_type", "resource_id"])
    op.create_index("ops_actions_action_idx", "ops_actions", ["action_type", "created_at"])


def downgrade() -> None:
    op.drop_index("ops_actions_action_idx", table_name="ops_actions")
    op.drop_index("ops_actions_resource_idx", table_name="ops_actions")
    op.drop_index("ops_actions_created_at_idx", table_name="ops_actions")
    op.drop_index("ops_actions_operator_id_idx", table_name="ops_actions")
    op.drop_index("ops_actions_action_type_idx", table_name="ops_actions")
    op.drop_table("ops_actions")

    op.drop_index("ops_dashboards_generated_at_idx", table_name="ops_dashboards")
    op.drop_table("ops_dashboards")

    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
