"""add reputation fields to npcs and quest_definitions

Revision ID: 2026_07_10_2200_add_reputation_fields
Revises: 2026_07_10_0200_add_npc_and_quest_tables
Create Date: 2026-07-10 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2026_07_10_2200_add_reputation_fields"
down_revision: Union[str, None] = "2026_07_10_0200_add_npc_and_quest_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "npcs",
        sa.Column(
            "min_reputation",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "npcs",
        sa.Column(
            "interaction_restrictions_jsonb",
            sa.JSON(),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "npcs_min_reputation_check",
        "npcs",
        "min_reputation >= 0",
    )
    op.create_index(
        "npcs_min_reputation_idx",
        "npcs",
        ["min_reputation"],
    )

    op.add_column(
        "quest_definitions",
        sa.Column(
            "min_reputation",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "quest_definitions",
        sa.Column(
            "required_reputation_level",
            sa.String(length=32),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "quest_definitions_min_reputation_check",
        "quest_definitions",
        "min_reputation >= 0",
    )
    op.create_index(
        "quest_definitions_min_reputation_idx",
        "quest_definitions",
        ["min_reputation"],
    )


def downgrade() -> None:
    op.drop_index("quest_definitions_min_reputation_idx", table_name="quest_definitions")
    op.drop_constraint("quest_definitions_min_reputation_check", "quest_definitions", type_="check")
    op.drop_column("quest_definitions", "required_reputation_level")
    op.drop_column("quest_definitions", "min_reputation")

    op.drop_index("npcs_min_reputation_idx", table_name="npcs")
    op.drop_constraint("npcs_min_reputation_check", "npcs", type_="check")
    op.drop_column("npcs", "interaction_restrictions_jsonb")
    op.drop_column("npcs", "min_reputation")
