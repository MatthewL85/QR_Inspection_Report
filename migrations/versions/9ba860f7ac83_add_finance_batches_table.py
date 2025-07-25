"""Add finance_batches table

Revision ID: 9ba860f7ac83
Revises: 142c3d343b26
Create Date: 2025-07-13 11:44:27.781693

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9ba860f7ac83'
down_revision = '142c3d343b26'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('finance_batches',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('client_id', sa.Integer(), nullable=False),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.Column('last_modified_by_id', sa.Integer(), nullable=True),
    sa.Column('batch_name', sa.String(length=150), nullable=False),
    sa.Column('batch_type', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('period_start', sa.Date(), nullable=False),
    sa.Column('period_end', sa.Date(), nullable=False),
    sa.Column('posted_at', sa.DateTime(), nullable=True),
    sa.Column('parsed_summary', sa.Text(), nullable=True),
    sa.Column('parsed_text', sa.Text(), nullable=True),
    sa.Column('extracted_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('ai_scorecard', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('is_ai_flagged', sa.Boolean(), nullable=True),
    sa.Column('gar_notes', sa.Text(), nullable=True),
    sa.Column('gar_context_reference', sa.String(length=100), nullable=True),
    sa.Column('context_tags', sa.ARRAY(sa.String(length=50)), nullable=True),
    sa.Column('role_visibility', sa.ARRAY(sa.String(length=50)), nullable=True),
    sa.Column('external_reference', sa.String(length=100), nullable=True),
    sa.Column('external_system', sa.String(length=100), nullable=True),
    sa.Column('sync_status', sa.String(length=50), nullable=True),
    sa.Column('last_synced_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('last_modified', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['last_modified_by_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('finance_batches', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_finance_batches_batch_name'), ['batch_name'], unique=False)
        batch_op.create_index(batch_op.f('ix_finance_batches_batch_type'), ['batch_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_finance_batches_client_id'), ['client_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_finance_batches_period_end'), ['period_end'], unique=False)
        batch_op.create_index(batch_op.f('ix_finance_batches_period_start'), ['period_start'], unique=False)
        batch_op.create_index(batch_op.f('ix_finance_batches_status'), ['status'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('finance_batches', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_finance_batches_status'))
        batch_op.drop_index(batch_op.f('ix_finance_batches_period_start'))
        batch_op.drop_index(batch_op.f('ix_finance_batches_period_end'))
        batch_op.drop_index(batch_op.f('ix_finance_batches_client_id'))
        batch_op.drop_index(batch_op.f('ix_finance_batches_batch_type'))
        batch_op.drop_index(batch_op.f('ix_finance_batches_batch_name'))

    op.drop_table('finance_batches')
    # ### end Alembic commands ###
