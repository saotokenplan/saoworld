"""add audit_logs table

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-07-04 02:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2a3b4c5d6e7'
down_revision: Union[str, Sequence[str], None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("audit_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("trace_id", sa.String(length=128), nullable=False, index=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("operator_id", sa.String(length=128), nullable=False),
        sa.Column("operator_role", sa.String(length=16), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("request_payload_jsonb", sa.JSON(), nullable=True),
        sa.Column("result_status", sa.SmallInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "operator_role IN ('player', 'ops', 'reviewer', 'system')",
            name="audit_logs_operator_role_check",
        ),
    )
    op.create_index("audit_logs_trace_id_idx", "audit_logs", ["trace_id"])
    op.create_index("audit_logs_operator_id_idx", "audit_logs", ["operator_id", "created_at"])
    op.create_index("audit_logs_resource_idx", "audit_logs", ["resource_type", "resource_id"])
    op.create_index("audit_logs_action_idx", "audit_logs", ["action", "created_at"])


def downgrade() -> None:
    op.drop_index("audit_logs_action_idx", table_name="audit_logs")
    op.drop_index("audit_logs_resource_idx", table_name="audit_logs")
    op.drop_index("audit_logs_operator_id_idx", table_name="audit_logs")
    op.drop_index("audit_logs_trace_id_idx", table_name="audit_logs")
    op.drop_table("audit_logs")
