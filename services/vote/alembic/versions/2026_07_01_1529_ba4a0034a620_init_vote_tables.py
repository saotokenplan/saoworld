"""init vote tables

Revision ID: ba4a0034a620
Revises: 
Create Date: 2026-07-01 15:29:07.060905

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba4a0034a620'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "vote_cycles",
        sa.Column("vote_cycle_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("chapter_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft", index=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=False),
        sa.Column("created_reason", sa.Text(), nullable=False),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("winning_candidate_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("ends_at > starts_at", name="vote_cycles_ends_after_starts"),
        sa.CheckConstraint(
            "status IN ('draft', 'scheduled', 'open', 'closed', 'finalized')",
            name="vote_cycles_status_check",
        ),
    )
    op.create_index("vote_cycles_chapter_id_idx", "vote_cycles", ["chapter_id"])
    op.create_index("vote_cycles_status_idx", "vote_cycles", ["status"])

    op.create_table(
        "vote_candidates",
        sa.Column("candidate_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("vote_cycle_id", sa.Uuid(), sa.ForeignKey("vote_cycles.vote_cycle_id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("region_scope", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("risk_tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("generated_params", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("vote_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('active', 'withdrawn', 'selected')",
            name="vote_candidates_status_check",
        ),
    )
    op.create_index("vote_candidates_cycle_id_idx", "vote_candidates", ["vote_cycle_id"])

    op.create_table(
        "votes",
        sa.Column("vote_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("vote_cycle_id", sa.Uuid(), sa.ForeignKey("vote_cycles.vote_cycle_id"), nullable=False),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), sa.ForeignKey("vote_candidates.candidate_id"), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("device_fingerprint_hash", sa.String(length=128), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("vote_cycle_id", "player_id", name="votes_cycle_player_uniq"),
        sa.CheckConstraint("weight > 0 AND weight <= 10.0", name="votes_weight_range"),
    )
    op.create_index("votes_candidate_id_idx", "votes", ["candidate_id"])
    op.create_index("votes_idempotency_key_idx", "votes", ["idempotency_key"], unique=True)


def downgrade() -> None:
    op.drop_index("votes_idempotency_key_idx", table_name="votes")
    op.drop_index("votes_candidate_id_idx", table_name="votes")
    op.drop_table("votes")

    op.drop_index("vote_candidates_cycle_id_idx", table_name="vote_candidates")
    op.drop_table("vote_candidates")

    op.drop_index("vote_cycles_status_idx", table_name="vote_cycles")
    op.drop_index("vote_cycles_chapter_id_idx", table_name="vote_cycles")
    op.drop_table("vote_cycles")

    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
