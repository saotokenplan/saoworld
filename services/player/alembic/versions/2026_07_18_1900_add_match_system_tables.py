"""add match system tables (M3-04)

Revision ID: 2026_07_18_1900
Revises: 2026_07_17_0801
Create Date: 2026-07-18 19:00:00.000000

为 M3-04 跨服匹配系统新增 5 张核心表：
- match_seasons: 匹配赛季表（不含 M3-05 扩展的 settlement_status/settled_at 字段）
- player_ratings: 玩家段位表
- match_queues: 匹配队列表
- match_rooms: 对战房间表
- match_results: 对战结果表

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "2026_07_18_1900"
down_revision: Union[str, None] = "2026_07_17_0801"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. match_seasons（M3-04 基础字段，不含 M3-05 的 settlement_status/settled_at）
    op.create_table(
        "match_seasons",
        sa.Column("season_id", sa.UUID(), nullable=False),
        sa.Column("season_key", sa.String(64), nullable=False),
        sa.Column("season_name", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="upcoming"),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reward_jsonb", sa.JSON(), nullable=True),
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
            "status IN ('upcoming', 'active', 'ended', 'archived')",
            name="match_seasons_status_check",
        ),
        sa.PrimaryKeyConstraint("season_id"),
        sa.UniqueConstraint("season_key", name="match_seasons_season_key_key"),
    )
    op.create_index("ix_match_seasons_status", "match_seasons", ["status"])
    op.create_index("match_seasons_status_idx", "match_seasons", ["status"])
    op.create_index("match_seasons_time_idx", "match_seasons", ["start_at", "end_at"])

    # 2. player_ratings
    op.create_table(
        "player_ratings",
        sa.Column("rating_id", sa.UUID(), nullable=False),
        sa.Column("player_id", sa.UUID(), nullable=False),
        sa.Column("season_id", sa.UUID(), nullable=False),
        sa.Column("tier", sa.String(32), nullable=False, server_default="bronze"),
        sa.Column("division", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("rating_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("wins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("losses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("draws", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("win_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("best_tier", sa.String(32), nullable=False, server_default="bronze"),
        sa.Column("best_division", sa.Integer(), nullable=False, server_default="5"),
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
            "tier IN ('bronze', 'silver', 'gold', 'platinum', 'diamond', 'master', 'challenger')",
            name="player_ratings_tier_check",
        ),
        sa.CheckConstraint("division >= 1 AND division <= 5", name="player_ratings_division_check"),
        sa.CheckConstraint("rating_points >= 0", name="player_ratings_points_check"),
        sa.CheckConstraint("wins >= 0", name="player_ratings_wins_check"),
        sa.CheckConstraint("losses >= 0", name="player_ratings_losses_check"),
        sa.CheckConstraint("draws >= 0", name="player_ratings_draws_check"),
        sa.CheckConstraint("win_streak >= 0", name="player_ratings_win_streak_check"),
        sa.PrimaryKeyConstraint("rating_id"),
    )
    op.create_index("ix_player_ratings_player_id", "player_ratings", ["player_id"])
    op.create_index("ix_player_ratings_season_id", "player_ratings", ["season_id"])
    op.create_index("ix_player_ratings_tier", "player_ratings", ["tier"])
    op.create_index(
        "player_ratings_player_season_idx",
        "player_ratings",
        ["player_id", "season_id"],
        unique=True,
    )
    op.create_index(
        "player_ratings_season_tier_idx",
        "player_ratings",
        ["season_id", "tier"],
    )

    # 3. match_queues
    op.create_table(
        "match_queues",
        sa.Column("queue_id", sa.UUID(), nullable=False),
        sa.Column("player_id", sa.UUID(), nullable=False),
        sa.Column("season_id", sa.UUID(), nullable=False),
        sa.Column("match_mode", sa.String(32), nullable=False, server_default="solo_1v1"),
        sa.Column("status", sa.String(32), nullable=False, server_default="queuing"),
        sa.Column("tier", sa.String(32), nullable=False, server_default="bronze"),
        sa.Column("division", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("player_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("matched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("match_room_id", sa.UUID(), nullable=True),
        sa.Column("timeout_at", sa.DateTime(timezone=True), nullable=False),
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
            "status IN ('queuing', 'matched', 'cancelled', 'timeout')",
            name="match_queues_status_check",
        ),
        sa.CheckConstraint(
            "match_mode IN ('solo_1v1', 'team_2v2', 'team_3v3')",
            name="match_queues_mode_check",
        ),
        sa.CheckConstraint(
            "tier IN ('bronze', 'silver', 'gold', 'platinum', 'diamond', 'master', 'challenger')",
            name="match_queues_tier_check",
        ),
        sa.CheckConstraint("division >= 1 AND division <= 5", name="match_queues_division_check"),
        sa.CheckConstraint("player_level >= 1", name="match_queues_level_check"),
        sa.PrimaryKeyConstraint("queue_id"),
    )
    op.create_index("ix_match_queues_player_id", "match_queues", ["player_id"])
    op.create_index("ix_match_queues_season_id", "match_queues", ["season_id"])
    op.create_index("ix_match_queues_match_mode", "match_queues", ["match_mode"])
    op.create_index("ix_match_queues_status", "match_queues", ["status"])
    op.create_index("ix_match_queues_match_room_id", "match_queues", ["match_room_id"])
    op.create_index(
        "match_queues_player_status_idx",
        "match_queues",
        ["player_id", "status"],
    )
    op.create_index(
        "match_queues_mode_status_idx",
        "match_queues",
        ["match_mode", "status"],
    )
    op.create_index("match_queues_joined_idx", "match_queues", ["joined_at"])

    # 4. match_rooms
    op.create_table(
        "match_rooms",
        sa.Column("room_id", sa.UUID(), nullable=False),
        sa.Column("season_id", sa.UUID(), nullable=False),
        sa.Column("match_mode", sa.String(32), nullable=False, server_default="solo_1v1"),
        sa.Column("status", sa.String(32), nullable=False, server_default="waiting"),
        sa.Column("player1_id", sa.UUID(), nullable=False),
        sa.Column("player2_id", sa.UUID(), nullable=False),
        sa.Column("player1_ready", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("player2_ready", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("winner_id", sa.UUID(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("match_data_jsonb", sa.JSON(), nullable=True),
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
            "status IN ('waiting', 'ready', 'in_progress', 'completed', 'cancelled')",
            name="match_rooms_status_check",
        ),
        sa.CheckConstraint(
            "match_mode IN ('solo_1v1', 'team_2v2', 'team_3v3')",
            name="match_rooms_mode_check",
        ),
        sa.CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds >= 0",
            name="match_rooms_duration_check",
        ),
        sa.PrimaryKeyConstraint("room_id"),
    )
    op.create_index("ix_match_rooms_season_id", "match_rooms", ["season_id"])
    op.create_index("ix_match_rooms_match_mode", "match_rooms", ["match_mode"])
    op.create_index("ix_match_rooms_status", "match_rooms", ["status"])
    op.create_index("ix_match_rooms_player1_id", "match_rooms", ["player1_id"])
    op.create_index("ix_match_rooms_player2_id", "match_rooms", ["player2_id"])
    op.create_index("ix_match_rooms_winner_id", "match_rooms", ["winner_id"])
    op.create_index(
        "match_rooms_season_status_idx",
        "match_rooms",
        ["season_id", "status"],
    )
    op.create_index(
        "match_rooms_player1_idx",
        "match_rooms",
        ["player1_id", "created_at"],
    )
    op.create_index(
        "match_rooms_player2_idx",
        "match_rooms",
        ["player2_id", "created_at"],
    )

    # 5. match_results
    op.create_table(
        "match_results",
        sa.Column("result_id", sa.UUID(), nullable=False),
        sa.Column("room_id", sa.UUID(), nullable=False),
        sa.Column("season_id", sa.UUID(), nullable=False),
        sa.Column("match_mode", sa.String(32), nullable=False, server_default="solo_1v1"),
        sa.Column("winner_id", sa.UUID(), nullable=True),
        sa.Column("loser_id", sa.UUID(), nullable=True),
        sa.Column("is_draw", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("winner_rating_change", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("loser_rating_change", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("winner_tier_before", sa.String(32), nullable=False),
        sa.Column("winner_division_before", sa.Integer(), nullable=False),
        sa.Column("winner_tier_after", sa.String(32), nullable=False),
        sa.Column("winner_division_after", sa.Integer(), nullable=False),
        sa.Column("loser_tier_before", sa.String(32), nullable=False),
        sa.Column("loser_division_before", sa.Integer(), nullable=False),
        sa.Column("loser_tier_after", sa.String(32), nullable=False),
        sa.Column("loser_division_after", sa.Integer(), nullable=False),
        sa.Column("match_data_jsonb", sa.JSON(), nullable=True),
        sa.Column("submitted_by", sa.UUID(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "match_mode IN ('solo_1v1', 'team_2v2', 'team_3v3')",
            name="match_results_mode_check",
        ),
        sa.PrimaryKeyConstraint("result_id"),
        sa.UniqueConstraint("room_id", name="match_results_room_id_key"),
    )
    op.create_index("ix_match_results_season_id", "match_results", ["season_id"])
    op.create_index("ix_match_results_match_mode", "match_results", ["match_mode"])
    op.create_index("ix_match_results_winner_id", "match_results", ["winner_id"])
    op.create_index("ix_match_results_loser_id", "match_results", ["loser_id"])
    op.create_index(
        "match_results_season_idx",
        "match_results",
        ["season_id", "created_at"],
    )
    op.create_index(
        "match_results_winner_idx",
        "match_results",
        ["winner_id", "created_at"],
    )
    op.create_index(
        "match_results_loser_idx",
        "match_results",
        ["loser_id", "created_at"],
    )


def downgrade() -> None:
    # match_results
    op.drop_index("match_results_loser_idx", table_name="match_results")
    op.drop_index("match_results_winner_idx", table_name="match_results")
    op.drop_index("match_results_season_idx", table_name="match_results")
    op.drop_index("ix_match_results_loser_id", table_name="match_results")
    op.drop_index("ix_match_results_winner_id", table_name="match_results")
    op.drop_index("ix_match_results_match_mode", table_name="match_results")
    op.drop_index("ix_match_results_season_id", table_name="match_results")
    op.drop_table("match_results")

    # match_rooms
    op.drop_index("match_rooms_player2_idx", table_name="match_rooms")
    op.drop_index("match_rooms_player1_idx", table_name="match_rooms")
    op.drop_index("match_rooms_season_status_idx", table_name="match_rooms")
    op.drop_index("ix_match_rooms_winner_id", table_name="match_rooms")
    op.drop_index("ix_match_rooms_player2_id", table_name="match_rooms")
    op.drop_index("ix_match_rooms_player1_id", table_name="match_rooms")
    op.drop_index("ix_match_rooms_status", table_name="match_rooms")
    op.drop_index("ix_match_rooms_match_mode", table_name="match_rooms")
    op.drop_index("ix_match_rooms_season_id", table_name="match_rooms")
    op.drop_table("match_rooms")

    # match_queues
    op.drop_index("match_queues_joined_idx", table_name="match_queues")
    op.drop_index("match_queues_mode_status_idx", table_name="match_queues")
    op.drop_index("match_queues_player_status_idx", table_name="match_queues")
    op.drop_index("ix_match_queues_match_room_id", table_name="match_queues")
    op.drop_index("ix_match_queues_status", table_name="match_queues")
    op.drop_index("ix_match_queues_match_mode", table_name="match_queues")
    op.drop_index("ix_match_queues_season_id", table_name="match_queues")
    op.drop_index("ix_match_queues_player_id", table_name="match_queues")
    op.drop_table("match_queues")

    # player_ratings
    op.drop_index("player_ratings_season_tier_idx", table_name="player_ratings")
    op.drop_index("player_ratings_player_season_idx", table_name="player_ratings")
    op.drop_index("ix_player_ratings_tier", table_name="player_ratings")
    op.drop_index("ix_player_ratings_season_id", table_name="player_ratings")
    op.drop_index("ix_player_ratings_player_id", table_name="player_ratings")
    op.drop_table("player_ratings")

    # match_seasons
    op.drop_index("match_seasons_time_idx", table_name="match_seasons")
    op.drop_index("match_seasons_status_idx", table_name="match_seasons")
    op.drop_index("ix_match_seasons_status", table_name="match_seasons")
    op.drop_table("match_seasons")
