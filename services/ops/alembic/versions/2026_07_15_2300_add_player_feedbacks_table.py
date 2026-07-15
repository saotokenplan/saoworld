"""Add player_feedbacks table

Revision ID: 2026_07_15_2300_add_player_feedbacks_table
Revises: 2026_07_14_1600_add_ops_events_table
Create Date: 2026-07-15 23:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2026_07_15_2300_add_player_feedbacks_table'
down_revision = '2026_07_14_1600_add_ops_events_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create player_feedbacks table
    op.create_table(
        'player_feedbacks',
        sa.Column('feedback_id', sa.UUID(), nullable=False),
        sa.Column('player_id', sa.String(128), nullable=False),
        sa.Column('feedback_type', sa.String(32), nullable=False),
        sa.Column('priority', sa.String(16), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(32), nullable=False, server_default='pending'),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('region_id', sa.String(128), nullable=True),
        sa.Column('chapter_id', sa.String(128), nullable=True),
        sa.Column('attachment_urls', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata_jsonb', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('resolved_by', sa.String(128), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_note', sa.Text(), nullable=True),
        sa.Column('trace_id', sa.String(128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "feedback_type IN ('bug', 'suggestion', 'question', 'other')",
            name='player_feedbacks_type_check',
        ),
        sa.CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'critical')",
            name='player_feedbacks_priority_check',
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'in_progress', 'resolved', 'closed')",
            name='player_feedbacks_status_check',
        ),
        sa.PrimaryKeyConstraint('feedback_id'),
    )

    # Create indexes
    op.create_index('ix_player_feedbacks_player_id', 'player_feedbacks', ['player_id'])
    op.create_index('ix_player_feedbacks_feedback_type', 'player_feedbacks', ['feedback_type'])
    op.create_index('ix_player_feedbacks_status', 'player_feedbacks', ['status'])
    op.create_index('ix_player_feedbacks_created_at', 'player_feedbacks', ['created_at'])
    op.create_index('player_feedbacks_player_idx', 'player_feedbacks', ['player_id', 'created_at'])
    op.create_index('player_feedbacks_status_created_idx', 'player_feedbacks', ['status', 'created_at'])
    op.create_index('player_feedbacks_type_created_idx', 'player_feedbacks', ['feedback_type', 'created_at'])


def downgrade() -> None:
    op.drop_index('player_feedbacks_type_created_idx', 'player_feedbacks')
    op.drop_index('player_feedbacks_status_created_idx', 'player_feedbacks')
    op.drop_index('player_feedbacks_player_idx', 'player_feedbacks')
    op.drop_index('ix_player_feedbacks_created_at', 'player_feedbacks')
    op.drop_index('ix_player_feedbacks_status', 'player_feedbacks')
    op.drop_index('ix_player_feedbacks_feedback_type', 'player_feedbacks')
    op.drop_index('ix_player_feedbacks_player_id', 'player_feedbacks')
    op.drop_table('player_feedbacks')