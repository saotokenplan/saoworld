"""add player_equipment table

Revision ID: 2026_07_14_1700_add_player_equipment
Revises: 2026_07_14_1300_add_guild_messages_table
Create Date: 2026-07-14 17:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026_07_14_1700_add_player_equipment"
down_revision: Union[str, None] = "2026_07_14_1300_add_guild_messages_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "player_equipment",
        sa.Column("equipment_id", sa.UUID(), nullable=False),
        sa.Column("player_id", sa.UUID(), nullable=False),
        sa.Column("slot", sa.String(length=32), nullable=False),
        sa.Column("item_key", sa.String(length=128), nullable=False),
        sa.Column("item_instance_id", sa.UUID(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stats_jsonb", sa.JSON(), nullable=True),
        sa.Column("equipped_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "slot IN ('head', 'chest', 'legs', 'feet', 'weapon', 'off_hand', 'ring', 'necklace')",
            name="player_equipment_slot_check",
        ),
        sa.CheckConstraint(
            "level >= 0",
            name="player_equipment_level_check",
        ),
        sa.PrimaryKeyConstraint("equipment_id"),
    )
    op.create_index(
        "player_equipment_player_slot_idx",
        "player_equipment",
        ["player_id", "slot"],
        unique=True,
    )
    op.create_index(
        "ix_player_equipment_player_id",
        "player_equipment",
        ["player_id"],
    )
    op.create_index(
        "ix_player_equipment_item_key",
        "player_equipment",
        ["item_key"],
    )
    op.create_index(
        "ix_player_equipment_slot",
        "player_equipment",
        ["slot"],
    )


def downgrade() -> None:
    op.drop_index("ix_player_equipment_slot", table_name="player_equipment")
    op.drop_index("ix_player_equipment_item_key", table_name="player_equipment")
    op.drop_index("ix_player_equipment_player_id", table_name="player_equipment")
    op.drop_index("player_equipment_player_slot_idx", table_name="player_equipment")
    op.drop_table("player_equipment")
