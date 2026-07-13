"""add_friendships_table

Revision ID: 2026_07_14_0900
Revises: g7h8i9j0k1l2
Create Date: 2026-07-14 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2026_07_14_0900'
down_revision: Union[str, Sequence[str], None] = 'g7h8i9j0k1l2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "friendships",
        sa.Column(
            "friendship_id",
            sa.uuid(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("player_id", sa.uuid(), nullable=False),
        sa.Column("friend_id", sa.uuid(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'accepted', 'rejected', 'blocked')",
            name="friendships_status_check",
        ),
    )
    op.create_index(
        "friendships_player_friend_idx",
        "friendships",
        ["player_id", "friend_id"],
        unique=True,
    )
    op.create_index(
        "friendships_friend_status_idx",
        "friendships",
        ["friend_id", "status"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("friendships_friend_status_idx", table_name="friendships")
    op.drop_index("friendships_player_friend_idx", table_name="friendships")
    op.drop_table("friendships")
