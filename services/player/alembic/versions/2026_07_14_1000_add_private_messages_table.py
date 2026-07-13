"""add private_messages table

Revision ID: 2026_07_14_1000
Revises: 2026_07_14_0900
Create Date: 2026-07-14 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2026_07_14_1000"
down_revision: Union[str, None] = "2026_07_14_0900"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "private_messages",
        sa.Column("message_id", sa.UUID(), nullable=False),
        sa.Column("sender_id", sa.UUID(), nullable=False),
        sa.Column("receiver_id", sa.UUID(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "length(content) > 0 AND length(content) <= 500",
            name="private_messages_content_check",
        ),
        sa.PrimaryKeyConstraint("message_id"),
    )
    op.create_index(
        "private_messages_sender_created_idx",
        "private_messages",
        ["sender_id", "created_at"],
    )
    op.create_index(
        "private_messages_receiver_created_idx",
        "private_messages",
        ["receiver_id", "created_at"],
    )
    op.create_index(
        "private_messages_conversation_idx",
        "private_messages",
        ["sender_id", "receiver_id"],
    )


def downgrade() -> None:
    op.drop_index("private_messages_conversation_idx", table_name="private_messages")
    op.drop_index("private_messages_receiver_created_idx", table_name="private_messages")
    op.drop_index("private_messages_sender_created_idx", table_name="private_messages")
    op.drop_table("private_messages")