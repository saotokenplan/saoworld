"""add_achievements

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-11 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "achievement_definitions",
        sa.Column("achievement_key", sa.String(length=128), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("icon", sa.String(length=256), nullable=True),
        sa.Column(
            "rarity",
            sa.String(length=32),
            nullable=False,
            server_default="common",
        ),
        sa.Column(
            "category",
            sa.String(length=32),
            nullable=False,
            server_default="quest",
        ),
        sa.Column(
            "points",
            sa.Integer(),
            nullable=False,
            server_default="10",
        ),
        sa.Column("reward_jsonb", sa.JSON(), nullable=True),
        sa.Column("condition_jsonb", sa.JSON(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "rarity IN ('common', 'uncommon', 'rare', 'epic', 'legendary')",
            name="achievement_definitions_rarity_check",
        ),
        sa.CheckConstraint(
            "category IN ('quest', 'exploration', 'combat', 'reputation', 'vote', 'social', 'collection')",
            name="achievement_definitions_category_check",
        ),
        sa.CheckConstraint(
            "points >= 0",
            name="achievement_definitions_points_check",
        ),
    )
    op.create_index(
        "achievement_definitions_category_idx",
        "achievement_definitions",
        ["category"],
    )
    op.create_index(
        "achievement_definitions_rarity_idx",
        "achievement_definitions",
        ["rarity"],
    )
    op.create_index(
        "achievement_definitions_is_active_idx",
        "achievement_definitions",
        ["is_active"],
    )

    op.create_table(
        "player_achievements",
        sa.Column(
            "player_achievement_id",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column("player_id", sa.Uuid(), nullable=False, index=True),
        sa.Column(
            "achievement_key",
            sa.String(length=128),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "unlocked_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "reward_claimed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "source",
            sa.String(length=32),
            nullable=False,
            server_default="system",
        ),
        sa.Column("source_id", sa.String(length=128), nullable=True),
        sa.CheckConstraint(
            "source IN ('quest', 'exploration', 'combat', 'reputation', 'vote', 'ops', 'system')",
            name="player_achievements_source_check",
        ),
    )
    op.create_index(
        "player_achievements_player_achievement_idx",
        "player_achievements",
        ["player_id", "achievement_key"],
        unique=True,
    )
    op.create_index(
        "player_achievements_player_unlocked_idx",
        "player_achievements",
        ["player_id", "unlocked_at"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "player_achievements_player_unlocked_idx",
        table_name="player_achievements",
    )
    op.drop_index(
        "player_achievements_player_achievement_idx",
        table_name="player_achievements",
    )
    op.drop_table("player_achievements")

    op.drop_index(
        "achievement_definitions_is_active_idx",
        table_name="achievement_definitions",
    )
    op.drop_index(
        "achievement_definitions_rarity_idx",
        table_name="achievement_definitions",
    )
    op.drop_index(
        "achievement_definitions_category_idx",
        table_name="achievement_definitions",
    )
    op.drop_table("achievement_definitions")
