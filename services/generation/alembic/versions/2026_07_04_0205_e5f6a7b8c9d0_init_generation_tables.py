"""init generation tables

Revision ID: e5f6a7b8c9d0
Revises:
Create Date: 2026-07-04 02:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "vote_cycles",
        sa.Column("vote_cycle_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "vote_candidates",
        sa.Column("candidate_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("vote_cycle_id", sa.Uuid(), sa.ForeignKey("vote_cycles.vote_cycle_id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "generation_requests",
        sa.Column("request_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("vote_cycle_id", sa.Uuid(), sa.ForeignKey("vote_cycles.vote_cycle_id"), nullable=True),
        sa.Column("source_candidate_id", sa.Uuid(), sa.ForeignKey("vote_candidates.candidate_id"), nullable=True),
        sa.Column("template_id", sa.String(length=128), nullable=False),
        sa.Column("input_payload_jsonb", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'succeeded', 'failed_retryable', 'failed_permanent')",
            name="generation_requests_status_check",
        ),
    )
    op.create_index("generation_requests_status_idx", "generation_requests", ["status"])
    op.create_index("generation_requests_trace_id_idx", "generation_requests", ["trace_id"])

    op.create_table(
        "generated_objects",
        sa.Column("object_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column(
            "request_id", sa.Uuid(),
            sa.ForeignKey("generation_requests.request_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("object_type", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("object_payload_jsonb", sa.JSON(), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending_review"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('pending_review', 'approved', 'rejected', 'needs_revision')",
            name="generated_objects_status_check",
        ),
        sa.CheckConstraint(
            "quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)",
            name="generated_objects_quality_score_check",
        ),
    )
    op.create_index("generated_objects_request_id_idx", "generated_objects", ["request_id"])
    op.create_index("generated_objects_status_idx", "generated_objects", ["status"])
    op.create_index("generated_objects_type_idx", "generated_objects", ["object_type"])


def downgrade() -> None:
    op.drop_index("generated_objects_type_idx", table_name="generated_objects")
    op.drop_index("generated_objects_status_idx", table_name="generated_objects")
    op.drop_index("generated_objects_request_id_idx", table_name="generated_objects")
    op.drop_table("generated_objects")

    op.drop_index("generation_requests_trace_id_idx", table_name="generation_requests")
    op.drop_index("generation_requests_status_idx", table_name="generation_requests")
    op.drop_table("generation_requests")

    op.drop_table("vote_candidates")
    op.drop_table("vote_cycles")

    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
