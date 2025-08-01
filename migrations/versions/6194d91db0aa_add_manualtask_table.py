"""Add ManualTask Table

Revision ID: 6194d91db0aa
Revises: ba32fa96b9c5
Create Date: 2025-07-15 20:54:34.280684

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6194d91db0aa'
down_revision = 'ba32fa96b9c5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('manual_tasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('client_id', sa.Integer(), nullable=False),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.Column('task_name', sa.String(length=150), nullable=False),
    sa.Column('task_category', sa.String(length=100), nullable=True),
    sa.Column('frequency', sa.String(length=50), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('due_date', sa.Date(), nullable=False),
    sa.Column('last_updated', sa.DateTime(), nullable=True),
    sa.Column('created_by', sa.String(length=120), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('region', sa.String(length=100), nullable=True),
    sa.Column('site_block_name', sa.String(length=100), nullable=True),
    sa.Column('tags', sa.String(length=255), nullable=True),
    sa.Column('visibility_scope', sa.String(length=100), nullable=True),
    sa.Column('consent_verified', sa.Boolean(), nullable=True),
    sa.Column('is_private', sa.Boolean(), nullable=True),
    sa.Column('shared_with_director', sa.Boolean(), nullable=True),
    sa.Column('external_reference', sa.String(length=100), nullable=True),
    sa.Column('source_system', sa.String(length=100), nullable=True),
    sa.Column('is_external', sa.Boolean(), nullable=True),
    sa.Column('sync_status', sa.String(length=50), nullable=True),
    sa.Column('parsed_summary', sa.Text(), nullable=True),
    sa.Column('extracted_data', sa.JSON(), nullable=True),
    sa.Column('parsing_status', sa.String(length=50), nullable=True),
    sa.Column('parsed_at', sa.DateTime(), nullable=True),
    sa.Column('parsed_by_ai_version', sa.String(length=50), nullable=True),
    sa.Column('ai_source_type', sa.String(length=50), nullable=True),
    sa.Column('is_ai_processed', sa.Boolean(), nullable=True),
    sa.Column('ai_profile_locked', sa.Boolean(), nullable=True),
    sa.Column('ai_confidence_score', sa.Float(), nullable=True),
    sa.Column('flagged_sections', sa.JSON(), nullable=True),
    sa.Column('ai_governance_recommendation', sa.Text(), nullable=True),
    sa.Column('ai_priority', sa.String(length=50), nullable=True),
    sa.Column('ai_flagged_risks', sa.Text(), nullable=True),
    sa.Column('is_ai_governance_compliant', sa.Boolean(), nullable=True),
    sa.Column('ai_alignment_score', sa.Float(), nullable=True),
    sa.Column('gar_chat_ready', sa.Boolean(), nullable=True),
    sa.Column('gar_feedback', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('manual_tasks')
    # ### end Alembic commands ###
