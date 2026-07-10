"""add_level_and_experience

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9d0e1
Create Date: 2026-07-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'g7h8i9j0k1l2'
down_revision: Union[str, Sequence[str], None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "players",
        sa.Column(
            "level",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.add_column(
        "players",
        sa.Column(
            "experience_points",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.create_check_constraint(
        "players_level_check",
        "players",
        "level >= 1",
    )
    op.create_check_constraint(
        "players_experience_points_check",
        "players",
        "experience_points >= 0",
    )
    op.create_index(
        "players_level_idx",
        "players",
        ["level"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("players_level_idx", table_name="players")
    op.drop_constraint(
        "players_experience_points_check",
        "players",
        type_="check",
    )
    op.drop_constraint(
        "players_level_check",
        "players",
        type_="check",
    )
    op.drop_column("players", "experience_points")
    op.drop_column("players", "level")
