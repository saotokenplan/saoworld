"""add npc and quest_definitions tables

Revision ID: 2026_07_10_0200_add_npc_and_quest_tables
Revises: 2026_07_06_0700_add_world_skeletons_table
Create Date: 2026-07-10 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2026_07_10_0200_add_npc_and_quest_tables"
down_revision: Union[str, None] = "2026_07_06_0700_add_world_skeletons_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "npcs",
        sa.Column("npc_id", sa.UUID(), nullable=False),
        sa.Column("npc_key", sa.String(length=128), nullable=False),
        sa.Column("chapter_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=True),
        sa.Column("faction_key", sa.String(length=128), nullable=True),
        sa.Column("role", sa.String(length=64), nullable=True),
        sa.Column("location_key", sa.String(length=128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("personality", sa.JSON(), nullable=True),
        sa.Column("dialogues", sa.JSON(), nullable=True),
        sa.Column("related_quests", sa.JSON(), nullable=True),
        sa.Column("rewards", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("npc_id"),
        sa.UniqueConstraint("npc_key", name="uq_npcs_npc_key"),
    )
    op.create_index("npcs_npc_key_idx", "npcs", ["npc_key"], unique=True)
    op.create_index("npcs_chapter_id_idx", "npcs", ["chapter_id"])
    op.create_index("npcs_faction_key_idx", "npcs", ["faction_key"])

    op.create_table(
        "quest_definitions",
        sa.Column("quest_id", sa.UUID(), nullable=False),
        sa.Column("quest_key", sa.String(length=128), nullable=False),
        sa.Column("chapter_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("quest_type", sa.String(length=32), nullable=False),
        sa.Column("region_key", sa.String(length=128), nullable=True),
        sa.Column("start_npc_key", sa.String(length=128), nullable=True),
        sa.Column("end_npc_key", sa.String(length=128), nullable=True),
        sa.Column("prerequisites", sa.JSON(), nullable=True),
        sa.Column("objectives", sa.JSON(), nullable=False),
        sa.Column("rewards", sa.JSON(), nullable=True),
        sa.Column("failure_condition", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("quest_id"),
        sa.UniqueConstraint("quest_key", name="uq_quest_definitions_quest_key"),
        sa.CheckConstraint(
            "quest_type IN ('main', 'side', 'event', 'daily')",
            name="quest_definitions_quest_type_check",
        ),
    )
    op.create_index("quest_definitions_quest_key_idx", "quest_definitions", ["quest_key"], unique=True)
    op.create_index("quest_definitions_chapter_id_idx", "quest_definitions", ["chapter_id"])
    op.create_index("quest_definitions_quest_type_idx", "quest_definitions", ["quest_type"])
    op.create_index("quest_definitions_region_key_idx", "quest_definitions", ["region_key"])


def downgrade() -> None:
    op.drop_index("quest_definitions_region_key_idx", table_name="quest_definitions")
    op.drop_index("quest_definitions_quest_type_idx", table_name="quest_definitions")
    op.drop_index("quest_definitions_chapter_id_idx", table_name="quest_definitions")
    op.drop_index("quest_definitions_quest_key_idx", table_name="quest_definitions")
    op.drop_table("quest_definitions")

    op.drop_index("npcs_faction_key_idx", table_name="npcs")
    op.drop_index("npcs_chapter_id_idx", table_name="npcs")
    op.drop_index("npcs_npc_key_idx", table_name="npcs")
    op.drop_table("npcs")
