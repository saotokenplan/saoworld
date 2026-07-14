"""add boss fields to monster_definitions table

Revision ID: 2026_07_14_2000_add_boss_fields
Revises: 2026_07_14_1700_add_item_definitions
Create Date: 2026-07-14 20:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "2026_07_14_2000_add_boss_fields"
down_revision: Union[str, None] = "2026_07_14_1700_add_item_definitions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "monster_definitions",
        sa.Column("is_boss", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "monster_definitions",
        sa.Column("boss_rank", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "monster_definitions",
        sa.Column("phase_count", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "monster_definitions",
        sa.Column("special_skills_jsonb", sa.JSON(), nullable=True),
    )
    op.add_column(
        "monster_definitions",
        sa.Column("enrage_threshold", sa.Float(), nullable=False, server_default="0.0"),
    )
    op.add_column(
        "monster_definitions",
        sa.Column("reward_jsonb", sa.JSON(), nullable=True),
    )

    op.create_check_constraint(
        "monster_definitions_boss_rank_check",
        "monster_definitions",
        "boss_rank IN ('legendary', 'mythic')",
    )
    op.create_check_constraint(
        "monster_definitions_phase_count_check",
        "monster_definitions",
        "phase_count >= 1",
    )
    op.create_check_constraint(
        "monster_definitions_enrage_threshold_check",
        "monster_definitions",
        "enrage_threshold >= 0 AND enrage_threshold <= 1",
    )

    op.create_index(
        "monster_definitions_is_boss_region_idx",
        "monster_definitions",
        ["is_boss", "region_key"],
    )
    op.create_index(
        "monster_definitions_is_boss_idx",
        "monster_definitions",
        ["is_boss"],
    )


def downgrade() -> None:
    op.drop_index("monster_definitions_is_boss_idx", table_name="monster_definitions")
    op.drop_index("monster_definitions_is_boss_region_idx", table_name="monster_definitions")

    op.drop_constraint(
        "monster_definitions_enrage_threshold_check",
        "monster_definitions",
        type_="check",
    )
    op.drop_constraint(
        "monster_definitions_phase_count_check",
        "monster_definitions",
        type_="check",
    )
    op.drop_constraint(
        "monster_definitions_boss_rank_check",
        "monster_definitions",
        type_="check",
    )

    op.drop_column("monster_definitions", "reward_jsonb")
    op.drop_column("monster_definitions", "enrage_threshold")
    op.drop_column("monster_definitions", "special_skills_jsonb")
    op.drop_column("monster_definitions", "phase_count")
    op.drop_column("monster_definitions", "boss_rank")
    op.drop_column("monster_definitions", "is_boss")