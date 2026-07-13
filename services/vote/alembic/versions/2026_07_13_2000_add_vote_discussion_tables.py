"""add vote discussion tables

Revision ID: f7a8b9c0d1e2
Revises: c8d2e5f1a730
Create Date: 2026-07-13 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f7a8b9c0d1e2'
down_revision: Union[str, Sequence[str], None] = 'c8d2e5f1a730'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vote_discussions",
        sa.Column("discussion_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column(
            "vote_cycle_id", sa.Uuid(),
            sa.ForeignKey("vote_cycles.vote_cycle_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reply_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("length(content) >= 1 AND length(content) <= 500", name="discussions_content_length"),
        sa.CheckConstraint(
            "status IN ('active', 'hidden', 'deleted')",
            name="discussions_status_check",
        ),
    )
    op.create_index("vote_discussions_cycle_id_idx", "vote_discussions", ["vote_cycle_id"])
    op.create_index("vote_discussions_player_id_idx", "vote_discussions", ["player_id"])
    op.create_index("vote_discussions_cycle_created_idx", "vote_discussions", ["vote_cycle_id", "created_at"])
    op.create_index("vote_discussions_cycle_likes_idx", "vote_discussions", ["vote_cycle_id", "like_count"])

    op.create_table(
        "vote_discussion_replies",
        sa.Column("reply_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column(
            "discussion_id", sa.Uuid(),
            sa.ForeignKey("vote_discussions.discussion_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("length(content) >= 1 AND length(content) <= 500", name="replies_content_length"),
        sa.CheckConstraint(
            "status IN ('active', 'hidden', 'deleted')",
            name="replies_status_check",
        ),
    )
    op.create_index("vote_discussion_replies_discussion_id_idx", "vote_discussion_replies", ["discussion_id"])
    op.create_index("vote_discussion_replies_player_id_idx", "vote_discussion_replies", ["player_id"])
    op.create_index(
        "vote_discussion_replies_discussion_created_idx",
        "vote_discussion_replies",
        ["discussion_id", "created_at"],
    )

    op.create_table(
        "vote_discussion_likes",
        sa.Column("like_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column(
            "discussion_id", sa.Uuid(),
            sa.ForeignKey("vote_discussions.discussion_id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "reply_id", sa.Uuid(),
            sa.ForeignKey("vote_discussion_replies.reply_id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("player_id", "discussion_id", name="vote_discussion_likes_player_discussion_uniq"),
        sa.UniqueConstraint("player_id", "reply_id", name="vote_discussion_likes_player_reply_uniq"),
    )


def downgrade() -> None:
    op.drop_table("vote_discussion_likes")

    op.drop_index("vote_discussion_replies_discussion_created_idx", table_name="vote_discussion_replies")
    op.drop_index("vote_discussion_replies_player_id_idx", table_name="vote_discussion_replies")
    op.drop_index("vote_discussion_replies_discussion_id_idx", table_name="vote_discussion_replies")
    op.drop_table("vote_discussion_replies")

    op.drop_index("vote_discussions_cycle_likes_idx", table_name="vote_discussions")
    op.drop_index("vote_discussions_cycle_created_idx", table_name="vote_discussions")
    op.drop_index("vote_discussions_player_id_idx", table_name="vote_discussions")
    op.drop_index("vote_discussions_cycle_id_idx", table_name="vote_discussions")
    op.drop_table("vote_discussions")
