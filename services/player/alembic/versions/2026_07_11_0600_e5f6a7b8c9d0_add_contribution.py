"""add_contribution

Revision ID: e5f6a7b8c9d0
Revises: a1b2c3d4e5f6
Create Date: 2026-07-11 06:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "players",
        sa.Column(
            "contribution_points",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.create_check_constraint(
        "players_contribution_points_check",
        "players",
        "contribution_points >= 0",
    )

    op.create_table(
        "player_contributions",
        sa.Column(
            "contribution_id",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column("player_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("amount > 0", name="player_contributions_amount_check"),
        sa.CheckConstraint(
            "source IN ('quest', 'vote', 'building', 'ops', 'system')",
            name="player_contributions_source_check",
        ),
    )
    op.create_index(
        "player_contributions_player_created_idx",
        "player_contributions",
        ["player_id", "created_at"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "player_contributions_player_created_idx",
        table_name="player_contributions",
    )
    op.drop_table("player_contributions")
    op.drop_constraint(
        "players_contribution_points_check",
        table_name="players",
        type_="check",
    )
    op.drop_column("players", "contribution_points")
