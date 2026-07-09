"""add token usage and cost columns to generation_requests

Revision ID: add_cost_columns
Revises: f6a7b8c9d0e1
Create Date: 2026-07-10 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'add_cost_columns'
down_revision: Union[str, Sequence[str], None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "generation_requests",
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "generation_requests",
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "generation_requests",
        sa.Column("total_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "generation_requests",
        sa.Column("cost_usd", sa.Float(), nullable=True),
    )
    op.create_index("generation_requests_cost_usd_idx", "generation_requests", ["cost_usd"])


def downgrade() -> None:
    op.drop_index("generation_requests_cost_usd_idx", table_name="generation_requests")
    op.drop_column("generation_requests", "cost_usd")
    op.drop_column("generation_requests", "total_tokens")
    op.drop_column("generation_requests", "completion_tokens")
    op.drop_column("generation_requests", "prompt_tokens")