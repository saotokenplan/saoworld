"""add guilds and guild_members tables

Revision ID: 2026_07_14_1100
Revises: 2026_07_14_1000
Create Date: 2026-07-14 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2026_07_14_1100"
down_revision: Union[str, None] = "2026_07_14_1000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建 guilds 表
    op.create_table(
        "guilds",
        sa.Column("guild_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("leader_id", sa.UUID(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("announcement", sa.Text(), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("member_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_members", sa.Integer(), nullable=False, server_default="50"),
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
            "length(name) > 0 AND length(name) <= 64",
            name="guilds_name_check",
        ),
        sa.CheckConstraint(
            "level >= 1",
            name="guilds_level_check",
        ),
        sa.CheckConstraint(
            "member_count >= 1",
            name="guilds_member_count_check",
        ),
        sa.CheckConstraint(
            "max_members >= 1",
            name="guilds_max_members_check",
        ),
        sa.CheckConstraint(
            "member_count <= max_members",
            name="guilds_capacity_check",
        ),
        sa.PrimaryKeyConstraint("guild_id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("guilds_leader_id_idx", "guilds", ["leader_id"])

    # 创建 guild_members 表
    op.create_table(
        "guild_members",
        sa.Column("guild_member_id", sa.UUID(), nullable=False),
        sa.Column("guild_id", sa.UUID(), nullable=False),
        sa.Column("player_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(16), nullable=False, server_default="member"),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "role IN ('leader', 'officer', 'member')",
            name="guild_members_role_check",
        ),
        sa.PrimaryKeyConstraint("guild_member_id"),
        sa.UniqueConstraint("player_id"),
    )
    op.create_index("guild_members_guild_id_idx", "guild_members", ["guild_id"])
    op.create_index("guild_members_player_id_idx", "guild_members", ["player_id"])
    op.create_index("guild_members_role_idx", "guild_members", ["role"])
    op.create_index(
        "guild_members_guild_joined_idx",
        "guild_members",
        ["guild_id", "joined_at"],
    )


def downgrade() -> None:
    op.drop_index("guild_members_guild_joined_idx", table_name="guild_members")
    op.drop_index("guild_members_role_idx", table_name="guild_members")
    op.drop_index("guild_members_player_id_idx", table_name="guild_members")
    op.drop_index("guild_members_guild_id_idx", table_name="guild_members")
    op.drop_table("guild_members")

    op.drop_index("guilds_leader_id_idx", table_name="guilds")
    op.drop_table("guilds")