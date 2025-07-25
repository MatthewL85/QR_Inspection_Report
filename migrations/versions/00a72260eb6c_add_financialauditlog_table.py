"""Add FinancialAuditLog table

Revision ID: 00a72260eb6c
Revises: b1d31f77797d
Create Date: 2025-07-14 22:11:40.287377

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '00a72260eb6c'
down_revision = 'b1d31f77797d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('financial_audit_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('action_type', sa.String(length=100), nullable=False),
    sa.Column('table_name', sa.String(length=100), nullable=False),
    sa.Column('record_id', sa.Integer(), nullable=False),
    sa.Column('field_changed', sa.String(length=100), nullable=True),
    sa.Column('previous_value', sa.Text(), nullable=True),
    sa.Column('new_value', sa.Text(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('user_role', sa.String(length=100), nullable=True),
    sa.Column('ip_address', sa.String(length=100), nullable=True),
    sa.Column('user_agent', sa.String(length=255), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('flagged_by_ai', sa.Boolean(), nullable=True),
    sa.Column('reason_for_flag', sa.String(length=255), nullable=True),
    sa.Column('ai_recommendation', sa.String(length=255), nullable=True),
    sa.Column('is_gar_verified', sa.Boolean(), nullable=True),
    sa.Column('gar_context_reference', sa.String(length=100), nullable=True),
    sa.Column('gar_flag_confidence', sa.Float(), nullable=True),
    sa.Column('parsed_summary', sa.Text(), nullable=True),
    sa.Column('extracted_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('ai_scorecard', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('context_tags', sa.ARRAY(sa.String(length=50)), nullable=True),
    sa.Column('role_visibility', sa.ARRAY(sa.String(length=50)), nullable=True),
    sa.Column('gar_chat_ready', sa.Boolean(), nullable=True),
    sa.Column('gar_feedback', sa.Text(), nullable=True),
    sa.Column('sync_status', sa.String(length=50), nullable=True),
    sa.Column('external_system', sa.String(length=100), nullable=True),
    sa.Column('external_reference', sa.String(length=100), nullable=True),
    sa.Column('last_synced_at', sa.DateTime(), nullable=True),
    sa.Column('is_data_protection_event', sa.Boolean(), nullable=True),
    sa.Column('linked_module', sa.String(length=100), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('financial_audit_logs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_financial_audit_logs_action_type'), ['action_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_financial_audit_logs_record_id'), ['record_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_financial_audit_logs_table_name'), ['table_name'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('financial_audit_logs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_financial_audit_logs_table_name'))
        batch_op.drop_index(batch_op.f('ix_financial_audit_logs_record_id'))
        batch_op.drop_index(batch_op.f('ix_financial_audit_logs_action_type'))

    op.drop_table('financial_audit_logs')
    # ### end Alembic commands ###
