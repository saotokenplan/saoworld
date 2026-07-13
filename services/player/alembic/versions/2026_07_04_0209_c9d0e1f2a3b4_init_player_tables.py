"""init player tables

Revision ID: c9d0e1f2a3b4
Revises:
Create Date: 2026-07-04 02:09:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d0e1f2a3b4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "players",
        sa.Column("player_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("reputation_snapshot", sa.JSON(), nullable=True),
        sa.Column("progress_jsonb", sa.JSON(), nullable=True),
        sa.Column("chapter_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "player_quests",
        sa.Column("player_quest_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("quest_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="available"),
        sa.Column("objectives_jsonb", sa.JSON(), nullable=True),
        sa.Column("rewards_jsonb", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('available', 'active', 'completed', 'failed')",
            name="player_quests_status_check",
        ),
    )
    op.create_index("player_quests_player_quest_idx", "player_quests", ["player_id", "quest_id"])

    op.create_table(
        "player_regions",
        sa.Column("player_region_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("region_id", sa.String(length=128), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reputation", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("player_regions_player_region_idx", "player_regions", ["player_id", "region_id"])


def downgrade() -> None:
    op.drop_index("player_regions_player_region_idx", table_name="player_regions")
    op.drop_table("player_regions")

    op.drop_index("player_quests_player_quest_idx", table_name="player_quests")
    op.drop_table("player_quests")

    op.drop_table("players")

    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
