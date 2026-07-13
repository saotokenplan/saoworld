"""Initialize gateway service tables

Revision ID: 2026_07_08_2200_init_gateway_tables
Revises:
Create Date: 2026-07-08 22:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_07_08_2200_init_gateway_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("audit_id", sa.UUID(), nullable=False),
        sa.Column("trace_id", sa.String(length=128), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("operator_id", sa.String(length=128), nullable=False),
        sa.Column("operator_role", sa.String(length=16), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.UUID(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("request_payload_jsonb", sa.JSON(), nullable=True),
        sa.Column("result_status", sa.SmallInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("audit_id"),
        sa.CheckConstraint(
            "operator_role IN ('player', 'ops', 'reviewer', 'system')",
            name="audit_logs_operator_role_check",
        ),
    )
    op.create_index("audit_logs_operator_id_idx", "audit_logs", ["operator_id", "created_at"])
    op.create_index("audit_logs_resource_idx", "audit_logs", ["resource_type", "resource_id"])
    op.create_index("audit_logs_action_idx", "audit_logs", ["action", "created_at"])
    op.create_index(op.f("ix_audit_logs_trace_id"), "audit_logs", ["trace_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_logs_trace_id"), table_name="audit_logs")
    op.drop_index("audit_logs_action_idx", table_name="audit_logs")
    op.drop_index("audit_logs_resource_idx", table_name="audit_logs")
    op.drop_index("audit_logs_operator_id_idx", table_name="audit_logs")
    op.drop_table("audit_logs")
