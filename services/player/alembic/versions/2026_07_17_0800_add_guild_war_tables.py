"""add guild_war and friend_collab_quest tables

Revision ID: 2026_07_17_0800
Revises: 2026_07_17_0000
Create Date: 2026-07-17 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_07_17_0800"
down_revision: Union[str, None] = "2026_07_17_0000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "guild_wars",
        sa.Column("war_id", sa.UUID(), nullable=False),
        sa.Column("challenger_guild_id", sa.UUID(), nullable=False),
        sa.Column("defender_guild_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="declared"),
        sa.Column("war_type", sa.String(32), nullable=False, server_default="territory"),
        sa.Column("declared_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("winner_guild_id", sa.UUID(), nullable=True),
        sa.Column("challenger_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("defender_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reward_jsonb", sa.JSON(), nullable=True),
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
            "status IN ('declared', 'accepted', 'in_progress', 'completed', 'cancelled')",
            name="guild_wars_status_check",
        ),
        sa.CheckConstraint(
            "war_type IN ('territory', 'resource', 'honor')",
            name="guild_wars_type_check",
        ),
        sa.CheckConstraint("challenger_score >= 0", name="guild_wars_challenger_score_check"),
        sa.CheckConstraint("defender_score >= 0", name="guild_wars_defender_score_check"),
        sa.PrimaryKeyConstraint("war_id"),
    )
    op.create_index("guild_wars_challenger_guild_id_idx", "guild_wars", ["challenger_guild_id"])
    op.create_index("guild_wars_defender_guild_id_idx", "guild_wars", ["defender_guild_id"])
    op.create_index("guild_wars_status_idx", "guild_wars", ["status"])
    op.create_index("guild_wars_war_type_idx", "guild_wars", ["war_type"])
    op.create_index("guild_wars_winner_guild_id_idx", "guild_wars", ["winner_guild_id"])
    op.create_index("guild_wars_challenger_status_idx", "guild_wars", ["challenger_guild_id", "status"])
    op.create_index("guild_wars_defender_status_idx", "guild_wars", ["defender_guild_id", "status"])

    op.create_table(
        "guild_war_participants",
        sa.Column("participant_id", sa.UUID(), nullable=False),
        sa.Column("war_id", sa.UUID(), nullable=False),
        sa.Column("guild_id", sa.UUID(), nullable=False),
        sa.Column("player_id", sa.UUID(), nullable=False),
        sa.Column("kills", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deaths", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("contribution_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
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
        sa.CheckConstraint("kills >= 0", name="guild_war_participants_kills_check"),
        sa.CheckConstraint("deaths >= 0", name="guild_war_participants_deaths_check"),
        sa.CheckConstraint("contribution_score >= 0", name="guild_war_participants_contribution_check"),
        sa.PrimaryKeyConstraint("participant_id"),
    )
    op.create_index("guild_war_participants_war_id_idx", "guild_war_participants", ["war_id"])
    op.create_index("guild_war_participants_guild_id_idx", "guild_war_participants", ["guild_id"])
    op.create_index("guild_war_participants_player_id_idx", "guild_war_participants", ["player_id"])
    op.create_index(
        "guild_war_participants_war_player_idx",
        "guild_war_participants",
        ["war_id", "player_id"],
        unique=True,
    )
    op.create_index(
        "guild_war_participants_war_guild_idx",
        "guild_war_participants",
        ["war_id", "guild_id"],
    )

    op.create_table(
        "friend_collab_quests",
        sa.Column("quest_id", sa.UUID(), nullable=False),
        sa.Column("initiator_id", sa.UUID(), nullable=False),
        sa.Column("friend_id", sa.UUID(), nullable=False),
        sa.Column("quest_type", sa.String(32), nullable=False, server_default="hunt"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending_invite"),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("objectives_jsonb", sa.JSON(), nullable=True),
        sa.Column("progress_jsonb", sa.JSON(), nullable=True),
        sa.Column("rewards_jsonb", sa.JSON(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
            "quest_type IN ('hunt', 'explore', 'collect', 'escort', 'challenge')",
            name="friend_collab_quests_type_check",
        ),
        sa.CheckConstraint(
            "status IN ('pending_invite', 'active', 'completed', 'failed', 'expired')",
            name="friend_collab_quests_status_check",
        ),
        sa.PrimaryKeyConstraint("quest_id"),
    )
    op.create_index("friend_collab_quests_initiator_id_idx", "friend_collab_quests", ["initiator_id"])
    op.create_index("friend_collab_quests_friend_id_idx", "friend_collab_quests", ["friend_id"])
    op.create_index("friend_collab_quests_quest_type_idx", "friend_collab_quests", ["quest_type"])
    op.create_index("friend_collab_quests_status_idx", "friend_collab_quests", ["status"])
    op.create_index(
        "friend_collab_quests_initiator_status_idx",
        "friend_collab_quests",
        ["initiator_id", "status"],
    )
    op.create_index(
        "friend_collab_quests_friend_status_idx",
        "friend_collab_quests",
        ["friend_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("friend_collab_quests_friend_status_idx", table_name="friend_collab_quests")
    op.drop_index("friend_collab_quests_initiator_status_idx", table_name="friend_collab_quests")
    op.drop_index("friend_collab_quests_status_idx", table_name="friend_collab_quests")
    op.drop_index("friend_collab_quests_quest_type_idx", table_name="friend_collab_quests")
    op.drop_index("friend_collab_quests_friend_id_idx", table_name="friend_collab_quests")
    op.drop_index("friend_collab_quests_initiator_id_idx", table_name="friend_collab_quests")
    op.drop_table("friend_collab_quests")

    op.drop_index("guild_war_participants_war_guild_idx", table_name="guild_war_participants")
    op.drop_index("guild_war_participants_war_player_idx", table_name="guild_war_participants")
    op.drop_index("guild_war_participants_player_id_idx", table_name="guild_war_participants")
    op.drop_index("guild_war_participants_guild_id_idx", table_name="guild_war_participants")
    op.drop_index("guild_war_participants_war_id_idx", table_name="guild_war_participants")
    op.drop_table("guild_war_participants")

    op.drop_index("guild_wars_defender_status_idx", table_name="guild_wars")
    op.drop_index("guild_wars_challenger_status_idx", table_name="guild_wars")
    op.drop_index("guild_wars_winner_guild_id_idx", table_name="guild_wars")
    op.drop_index("guild_wars_war_type_idx", table_name="guild_wars")
    op.drop_index("guild_wars_status_idx", table_name="guild_wars")
    op.drop_index("guild_wars_defender_guild_id_idx", table_name="guild_wars")
    op.drop_index("guild_wars_challenger_guild_id_idx", table_name="guild_wars")
    op.drop_table("guild_wars")
