"""add guild_quests and guild_quest_progress tables

Revision ID: 2026_07_16_1800
Revises: 2026_07_14_1700_add_player_equipment
Create Date: 2026-07-16 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_07_16_1800"
down_revision: Union[str, None] = "2026_07_14_1700_add_player_equipment"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "guild_quests",
        sa.Column("guild_quest_id", sa.UUID(), nullable=False),
        sa.Column("guild_id", sa.UUID(), nullable=False),
        sa.Column("quest_key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("quest_type", sa.String(32), nullable=False, server_default="collect"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("objectives_jsonb", sa.JSON(), nullable=True),
        sa.Column("rewards_jsonb", sa.JSON(), nullable=True),
        sa.Column("progress_target", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("current_progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("time_limit_minutes", sa.Integer(), nullable=False, server_default="1440"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
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
            "quest_type IN ('collect', 'kill', 'deliver', 'explore', 'defend', 'craft')",
            name="guild_quests_type_check",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'completed', 'failed', 'expired')",
            name="guild_quests_status_check",
        ),
        sa.CheckConstraint("progress_target > 0", name="guild_quests_target_check"),
        sa.CheckConstraint("current_progress >= 0", name="guild_quests_progress_check"),
        sa.CheckConstraint("time_limit_minutes > 0", name="guild_quests_time_check"),
        sa.PrimaryKeyConstraint("guild_quest_id"),
    )
    op.create_index("guild_quests_guild_id_idx", "guild_quests", ["guild_id"])
    op.create_index("guild_quests_quest_key_idx", "guild_quests", ["quest_key"])
    op.create_index("guild_quests_quest_type_idx", "guild_quests", ["quest_type"])
    op.create_index("guild_quests_status_idx", "guild_quests", ["status"])
    op.create_index(
        "guild_quests_guild_status_idx",
        "guild_quests",
        ["guild_id", "status"],
    )
    op.create_index(
        "guild_quests_guild_key_idx",
        "guild_quests",
        ["guild_id", "quest_key"],
        unique=True,
    )

    op.create_table(
        "guild_quest_progress",
        sa.Column("progress_id", sa.UUID(), nullable=False),
        sa.Column("guild_quest_id", sa.UUID(), nullable=False),
        sa.Column("player_id", sa.UUID(), nullable=False),
        sa.Column("contribution", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("claimed_reward", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint("contribution >= 0", name="guild_quest_progress_contribution_check"),
        sa.PrimaryKeyConstraint("progress_id"),
    )
    op.create_index("guild_quest_progress_guild_quest_id_idx", "guild_quest_progress", ["guild_quest_id"])
    op.create_index("guild_quest_progress_player_id_idx", "guild_quest_progress", ["player_id"])
    op.create_index(
        "guild_quest_progress_player_idx",
        "guild_quest_progress",
        ["player_id", "guild_quest_id"],
        unique=True,
    )
    op.create_index(
        "guild_quest_progress_quest_idx",
        "guild_quest_progress",
        ["guild_quest_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("guild_quest_progress_quest_idx", table_name="guild_quest_progress")
    op.drop_index("guild_quest_progress_player_idx", table_name="guild_quest_progress")
    op.drop_index("guild_quest_progress_player_id_idx", table_name="guild_quest_progress")
    op.drop_index("guild_quest_progress_guild_quest_id_idx", table_name="guild_quest_progress")
    op.drop_table("guild_quest_progress")

    op.drop_index("guild_quests_guild_key_idx", table_name="guild_quests")
    op.drop_index("guild_quests_guild_status_idx", table_name="guild_quests")
    op.drop_index("guild_quests_status_idx", table_name="guild_quests")
    op.drop_index("guild_quests_quest_type_idx", table_name="guild_quests")
    op.drop_index("guild_quests_quest_key_idx", table_name="guild_quests")
    op.drop_index("guild_quests_guild_id_idx", table_name="guild_quests")
    op.drop_table("guild_quests")