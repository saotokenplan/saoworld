"""add item_definitions table

Revision ID: 2026_07_14_1700_add_item_definitions
Revises: 2026_07_10_2200_add_reputation_fields
Create Date: 2026-07-14 17:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026_07_14_1700_add_item_definitions"
down_revision: Union[str, None] = "2026_07_10_2200_add_reputation_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "item_definitions",
        sa.Column("item_id", sa.UUID(), nullable=False),
        sa.Column("item_key", sa.String(length=128), nullable=False),
        sa.Column("item_type", sa.String(length=32), nullable=False),
        sa.Column("item_slot", sa.String(length=32), nullable=True),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("rarity", sa.String(length=32), nullable=False),
        sa.Column("chapter_id", sa.String(length=64), nullable=False),
        sa.Column("level_requirement", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("stats_jsonb", sa.JSON(), nullable=True),
        sa.Column("effects_jsonb", sa.JSON(), nullable=True),
        sa.Column("sell_price", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stackable", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "item_type IN ('weapon', 'armor', 'accessory', 'consumable', 'material')",
            name="item_definitions_item_type_check",
        ),
        sa.CheckConstraint(
            "item_slot IN ('head', 'chest', 'legs', 'feet', 'weapon', 'off_hand', 'ring', 'necklace')",
            name="item_definitions_item_slot_check",
        ),
        sa.CheckConstraint(
            "rarity IN ('common', 'uncommon', 'rare', 'epic', 'legendary')",
            name="item_definitions_rarity_check",
        ),
        sa.PrimaryKeyConstraint("item_id"),
        sa.UniqueConstraint("item_key", name="item_definitions_item_key_key"),
    )
    op.create_index(
        "ix_item_definitions_item_key",
        "item_definitions",
        ["item_key"],
        unique=True,
    )
    op.create_index(
        "ix_item_definitions_item_type",
        "item_definitions",
        ["item_type"],
    )
    op.create_index(
        "ix_item_definitions_item_slot",
        "item_definitions",
        ["item_slot"],
    )
    op.create_index(
        "ix_item_definitions_rarity",
        "item_definitions",
        ["rarity"],
    )
    op.create_index(
        "ix_item_definitions_chapter_id",
        "item_definitions",
        ["chapter_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_item_definitions_chapter_id", table_name="item_definitions")
    op.drop_index("ix_item_definitions_rarity", table_name="item_definitions")
    op.drop_index("ix_item_definitions_item_slot", table_name="item_definitions")
    op.drop_index("ix_item_definitions_item_type", table_name="item_definitions")
    op.drop_index("ix_item_definitions_item_key", table_name="item_definitions")
    op.drop_table("item_definitions")
