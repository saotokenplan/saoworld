"""init review tables

Revision ID: a7b8c9d0e1f2
Revises: 
Create Date: 2026-07-04 02:07:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "review_records",
        sa.Column("review_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("object_id", sa.Uuid(), nullable=False),
        sa.Column("object_type", sa.String(length=64), nullable=False),
        sa.Column("review_type", sa.String(length=32), nullable=False),
        sa.Column("result", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("risk_level", sa.String(length=16), nullable=False, server_default="low"),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("detail_jsonb", sa.JSON(), nullable=True),
        sa.Column("operator_id", sa.String(length=128), nullable=True),
        sa.Column("operator_role", sa.String(length=16), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "result IN ('pending', 'approved', 'rejected', 'manual_review')",
            name="review_records_result_check",
        ),
        sa.CheckConstraint(
            "risk_level IN ('low', 'medium', 'high', 'critical')",
            name="review_records_risk_level_check",
        ),
        sa.CheckConstraint(
            "quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)",
            name="review_records_quality_score_check",
        ),
    )
    op.create_index("review_records_object_id_idx", "review_records", ["object_id"])
    op.create_index("review_records_result_idx", "review_records", ["result"])
    op.create_index("review_records_risk_level_idx", "review_records", ["risk_level"])
    op.create_index("review_records_review_type_idx", "review_records", ["review_type"])
    op.create_index("review_records_trace_id_idx", "review_records", ["trace_id"])


def downgrade() -> None:
    op.drop_index("review_records_trace_id_idx", table_name="review_records")
    op.drop_index("review_records_review_type_idx", table_name="review_records")
    op.drop_index("review_records_risk_level_idx", table_name="review_records")
    op.drop_index("review_records_result_idx", table_name="review_records")
    op.drop_index("review_records_object_id_idx", table_name="review_records")
    op.drop_table("review_records")

    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
