"""add vote anomalies table

Revision ID: a1b2c3d4e5f6
Revises: f7a8b9c0d1e2
Create Date: 2026-07-14 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f7a8b9c0d1e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vote_anomalies",
        sa.Column("anomaly_id", sa.Uuid(), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column(
            "vote_cycle_id", sa.Uuid(),
            sa.ForeignKey("vote_cycles.vote_cycle_id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("player_id", sa.Uuid(), nullable=False, index=True),
        sa.Column(
            "vote_id", sa.Uuid(),
            sa.ForeignKey("votes.vote_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("anomaly_type", sa.String(length=32), nullable=False, index=True),
        sa.Column("severity", sa.String(length=32), nullable=False, index=True),
        sa.Column(
            "status", sa.String(length=32),
            nullable=False, server_default="detected", index=True,
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("detail_jsonb", sa.JSON(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolver_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "anomaly_type IN ('frequency', 'device', 'weight', 'time_distribution', 'suspicious_pattern')",
            name="vote_anomalies_type_check",
        ),
        sa.CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="vote_anomalies_severity_check",
        ),
        sa.CheckConstraint(
            "status IN ('detected', 'reviewed', 'resolved', 'false_positive')",
            name="vote_anomalies_status_check",
        ),
    )
    op.create_index(
        "vote_anomalies_cycle_severity_idx",
        "vote_anomalies",
        ["vote_cycle_id", "severity"],
    )
    op.create_index(
        "vote_anomalies_detected_at_idx",
        "vote_anomalies",
        ["detected_at"],
    )


def downgrade() -> None:
    op.drop_index("vote_anomalies_detected_at_idx", table_name="vote_anomalies")
    op.drop_index("vote_anomalies_cycle_severity_idx", table_name="vote_anomalies")
    op.drop_table("vote_anomalies")
