"""init world tables

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2026-07-04 02:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "regions",
        sa.Column("region_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("chapter_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="locked", index=True),
        sa.Column("visible", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("unlock_condition_jsonb", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('locked', 'active', 'unstable', 'archived')",
            name="regions_status_check",
        ),
    )
    op.create_index("regions_chapter_id_idx", "regions", ["chapter_id"])
    op.create_index("regions_status_idx", "regions", ["status"])


def downgrade() -> None:
    op.drop_index("regions_status_idx", table_name="regions")
    op.drop_index("regions_chapter_id_idx", table_name="regions")
    op.drop_table("regions")

    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
