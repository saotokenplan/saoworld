"""add season reward grants and match_seasons settlement fields (M3-05)

Revision ID: 2026_07_18_1901
Revises: 2026_07_18_1900
Create Date: 2026-07-18 19:01:00.000000

为 M3-05 赛季排行系统新增：
- match_seasons 表扩展 settlement_status/settled_at 字段及对应 CHECK 约束与索引
- season_reward_grants 表（赛季奖励发放记录，append-only 风格，支持幂等）

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "2026_07_18_1901"
down_revision: Union[str, None] = "2026_07_18_1900"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 扩展 match_seasons 表：新增 settlement_status 与 settled_at 字段
    op.add_column(
        "match_seasons",
        sa.Column(
            "settlement_status",
            sa.String(32),
            nullable=False,
            server_default="unsettled",
        ),
    )
    op.add_column(
        "match_seasons",
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "match_seasons_settlement_status_check",
        "match_seasons",
        "settlement_status IN ('unsettled', 'settling', 'settled')",
    )
    op.create_index(
        "ix_match_seasons_settlement_status",
        "match_seasons",
        ["settlement_status"],
    )
    op.create_index(
        "match_seasons_settlement_idx",
        "match_seasons",
        ["settlement_status"],
    )

    # 2. 新增 season_reward_grants 表
    op.create_table(
        "season_reward_grants",
        sa.Column("grant_id", sa.UUID(), nullable=False),
        sa.Column("season_id", sa.UUID(), nullable=False),
        sa.Column("player_id", sa.UUID(), nullable=False),
        sa.Column("final_rank", sa.Integer(), nullable=False),
        sa.Column("final_tier", sa.String(32), nullable=False),
        sa.Column("final_division", sa.Integer(), nullable=False),
        sa.Column("final_rating_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reward_payload_jsonb", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("trace_id", sa.String(64), nullable=True),
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
            "final_tier IN ('bronze', 'silver', 'gold', 'platinum', 'diamond', 'master', 'challenger')",
            name="season_reward_grants_tier_check",
        ),
        sa.CheckConstraint(
            "final_division >= 1 AND final_division <= 5",
            name="season_reward_grants_division_check",
        ),
        sa.CheckConstraint(
            "final_rank >= 1",
            name="season_reward_grants_rank_check",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'granted', 'failed')",
            name="season_reward_grants_status_check",
        ),
        sa.PrimaryKeyConstraint("grant_id"),
        sa.UniqueConstraint("idempotency_key", name="season_reward_grants_idempotency_key_key"),
    )
    op.create_index(
        "ix_season_reward_grants_season_id",
        "season_reward_grants",
        ["season_id"],
    )
    op.create_index(
        "ix_season_reward_grants_player_id",
        "season_reward_grants",
        ["player_id"],
    )
    op.create_index(
        "ix_season_reward_grants_status",
        "season_reward_grants",
        ["status"],
    )
    op.create_index(
        "season_reward_grants_season_player_idx",
        "season_reward_grants",
        ["season_id", "player_id"],
        unique=True,
    )
    op.create_index(
        "season_reward_grants_season_rank_idx",
        "season_reward_grants",
        ["season_id", "final_rank"],
    )
    op.create_index(
        "season_reward_grants_player_idx",
        "season_reward_grants",
        ["player_id", "created_at"],
    )


def downgrade() -> None:
    # season_reward_grants
    op.drop_index(
        "season_reward_grants_player_idx",
        table_name="season_reward_grants",
    )
    op.drop_index(
        "season_reward_grants_season_rank_idx",
        table_name="season_reward_grants",
    )
    op.drop_index(
        "season_reward_grants_season_player_idx",
        table_name="season_reward_grants",
    )
    op.drop_index(
        "ix_season_reward_grants_status",
        table_name="season_reward_grants",
    )
    op.drop_index(
        "ix_season_reward_grants_player_id",
        table_name="season_reward_grants",
    )
    op.drop_index(
        "ix_season_reward_grants_season_id",
        table_name="season_reward_grants",
    )
    op.drop_table("season_reward_grants")

    # match_seasons 字段回滚
    op.drop_index(
        "match_seasons_settlement_idx",
        table_name="match_seasons",
    )
    op.drop_index(
        "ix_match_seasons_settlement_status",
        table_name="match_seasons",
    )
    op.drop_constraint(
        "match_seasons_settlement_status_check",
        "match_seasons",
        type_="check",
    )
    op.drop_column("match_seasons", "settled_at")
    op.drop_column("match_seasons", "settlement_status")
