"""add player_inventories table

Revision ID: a1b2c3d4e5f6
Revises: d0e1f2a3b4c5
Create Date: 2026-07-10 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'd0e1f2a3b4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "player_inventories",
        sa.Column("inventory_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("item_key", sa.String(length=128), nullable=False),
        sa.Column("item_type", sa.String(length=32), nullable=False, server_default="material"),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("metadata_jsonb", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "item_type IN ('consumable', 'equipment', 'material', 'quest_item')",
            name="player_inventories_item_type_check",
        ),
        sa.CheckConstraint(
            "quantity > 0",
            name="player_inventories_quantity_check",
        ),
    )
    op.create_index("ix_player_inventories_player_id", "player_inventories", ["player_id"])
    op.create_index(
        "player_inventories_player_item_idx",
        "player_inventories",
        ["player_id", "item_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("player_inventories_player_item_idx", table_name="player_inventories")
    op.drop_index("ix_player_inventories_player_id", table_name="player_inventories")
    op.drop_table("player_inventories")
