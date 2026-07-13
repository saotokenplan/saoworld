"""init content tables

Revision ID: c3d4e5f6a7b8
Revises:
Create Date: 2026-07-04 02:03:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
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

    op.create_table(
        "vote_cycles",
        sa.Column("vote_cycle_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "content_packages",
        sa.Column("content_package_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("chapter_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("region_id", sa.Uuid(), sa.ForeignKey("regions.region_id"), nullable=True, index=True),
        sa.Column("package_version", sa.String(length=32), nullable=False),
        sa.Column("source_vote_cycle_id", sa.Uuid(), sa.ForeignKey("vote_cycles.vote_cycle_id"), nullable=True),
        sa.Column("source_request_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="packaged", index=True),
        sa.Column("gray_scope_jsonb", sa.JSON(), nullable=True),
        sa.Column("payload_jsonb", sa.JSON(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('packaged', 'gray', 'live', 'archived', 'rolled_back')",
            name="content_packages_status_check",
        ),
    )
    op.create_index("content_packages_chapter_id_idx", "content_packages", ["chapter_id"])
    op.create_index("content_packages_status_idx", "content_packages", ["status"])
    op.create_index("content_packages_region_id_idx", "content_packages", ["region_id"])

    op.create_table(
        "release_records",
        sa.Column("release_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column(
            "content_package_id", sa.Uuid(),
            sa.ForeignKey("content_packages.content_package_id"),
            nullable=False, index=True,
        ),
        sa.Column("release_mode", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="queued"),
        sa.Column("gray_scope_jsonb", sa.JSON(), nullable=True),
        sa.Column("operator_id", sa.String(length=128), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("trace_id", sa.String(length=128), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "release_mode IN ('gray', 'full')",
            name="release_records_release_mode_check",
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'completed', 'failed')",
            name="release_records_status_check",
        ),
    )

    op.create_table(
        "rollback_records",
        sa.Column("rollback_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column(
            "content_package_id", sa.Uuid(),
            sa.ForeignKey("content_packages.content_package_id"),
            nullable=False, index=True,
        ),
        sa.Column("target_version", sa.String(length=32), nullable=False),
        sa.Column("rollback_reason", sa.Text(), nullable=False),
        sa.Column("operator_type", sa.String(length=16), nullable=False, server_default="ops"),
        sa.Column("operator_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="queued"),
        sa.Column("trace_id", sa.String(length=128), nullable=False),
        sa.Column("rolled_back_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "operator_type IN ('ops', 'system')",
            name="rollback_records_operator_type_check",
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'completed', 'failed')",
            name="rollback_records_status_check",
        ),
    )


def downgrade() -> None:
    op.drop_table("rollback_records")
    op.drop_table("release_records")
    op.drop_index("content_packages_region_id_idx", table_name="content_packages")
    op.drop_index("content_packages_status_idx", table_name="content_packages")
    op.drop_index("content_packages_chapter_id_idx", table_name="content_packages")
    op.drop_table("content_packages")
    op.drop_table("vote_cycles")
    op.drop_index("regions_status_idx", table_name="regions")
    op.drop_index("regions_chapter_id_idx", table_name="regions")
    op.drop_table("regions")

    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
