"""add world_skeletons table

Revision ID: 2026_07_06_0700_add_world_skeletons_table
Revises: 2026_07_04_0202_b2c3d4e5f6a7
Create Date: 2026-07-06 07:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2026_07_06_0700_add_world_skeletons_table"
down_revision: Union[str, None] = "2026_07_04_0202_b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "world_skeletons",
        sa.Column("skeleton_id", sa.UUID(), nullable=False),
        sa.Column("world_version", sa.String(length=64), nullable=False),
        sa.Column("chapter_id", sa.String(length=64), nullable=False),
        sa.Column("regions", sa.JSON(), nullable=False),
        sa.Column("factions", sa.JSON(), nullable=False),
        sa.Column("reserved_characters", sa.JSON(), nullable=True),
        sa.Column("forbidden_tags", sa.JSON(), nullable=False),
        sa.Column("reward_limits", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("skeleton_id"),
        sa.UniqueConstraint("world_version"),
    )
    op.create_index("world_skeletons_world_version_idx", "world_skeletons", ["world_version"])
    op.create_index("world_skeletons_chapter_id_idx", "world_skeletons", ["chapter_id"])
    op.create_index("world_skeletons_is_active_idx", "world_skeletons", ["is_active"])


def downgrade() -> None:
    op.drop_index("world_skeletons_is_active_idx", table_name="world_skeletons")
    op.drop_index("world_skeletons_chapter_id_idx", table_name="world_skeletons")
    op.drop_index("world_skeletons_world_version_idx", table_name="world_skeletons")
    op.drop_table("world_skeletons")