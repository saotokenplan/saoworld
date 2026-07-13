"""Add guild_messages table

Revision ID: 2026_07_14_1300_add_guild_messages_table
Revises:
Create Date: 2026-07-14 13:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026_07_14_1300_add_guild_messages_table"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "guild_messages",
        sa.Column("message_id", sa.UUID(), nullable=False),
        sa.Column("guild_id", sa.UUID(), nullable=False),
        sa.Column("sender_id", sa.UUID(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("message_id"),
        sa.CheckConstraint(
            "length(content) > 0 AND length(content) <= 500",
            name="guild_messages_content_check",
        ),
    )
    op.create_index(
        "guild_messages_guild_created_idx",
        "guild_messages",
        ["guild_id", "created_at"],
    )
    op.create_index(
        "guild_messages_sender_created_idx",
        "guild_messages",
        ["sender_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("guild_messages")