"""add player_events table

Revision ID: 2026_07_09_1400
Revises: f2a3b4c5d6e7
Create Date: 2026-07-09 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2026_07_09_1400'
down_revision: Union[str, Sequence[str], None] = 'f2a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "player_events",
        sa.Column("event_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("event_type", sa.String(length=64), nullable=False, index=True),
        sa.Column("player_id", sa.String(length=128), nullable=False, index=True),
        sa.Column("region_id", sa.String(length=128), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column("payload_jsonb", sa.JSON(), nullable=True),
        sa.Column("trace_id", sa.String(length=128), nullable=True),
        sa.Column("producer", sa.String(length=64), nullable=False, server_default="gateway"),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("player_events_player_idx", "player_events", ["player_id", "occurred_at"])
    op.create_index("player_events_region_idx", "player_events", ["region_id", "occurred_at"])
    op.create_index("player_events_type_idx", "player_events", ["event_type", "occurred_at"])


def downgrade() -> None:
    op.drop_index("player_events_type_idx", table_name="player_events")
    op.drop_index("player_events_region_idx", table_name="player_events")
    op.drop_index("player_events_player_idx", table_name="player_events")
    op.drop_table("player_events")
