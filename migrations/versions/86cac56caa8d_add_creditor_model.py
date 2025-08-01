"""Add Creditor model

Revision ID: 86cac56caa8d
Revises: 3f39a691575f
Create Date: 2025-07-14 22:05:44.003254

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '86cac56caa8d'
down_revision = '3f39a691575f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('creditors',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('company_name', sa.String(length=255), nullable=False),
    sa.Column('registration_number', sa.String(length=100), nullable=True),
    sa.Column('vat_number', sa.String(length=100), nullable=True),
    sa.Column('business_type', sa.String(length=100), nullable=True),
    sa.Column('email', sa.String(length=150), nullable=False),
    sa.Column('phone', sa.String(length=50), nullable=True),
    sa.Column('contact_name', sa.String(length=150), nullable=True),
    sa.Column('address', sa.Text(), nullable=True),
    sa.Column('default_currency', sa.String(length=10), nullable=True),
    sa.Column('account_reference', sa.String(length=100), nullable=True),
    sa.Column('payment_terms', sa.String(length=100), nullable=True),
    sa.Column('contract_document', sa.String(length=255), nullable=True),
    sa.Column('insurance_expiry', sa.Date(), nullable=True),
    sa.Column('health_safety_expiry', sa.Date(), nullable=True),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('parsed_summary', sa.Text(), nullable=True),
    sa.Column('parsed_text', sa.Text(), nullable=True),
    sa.Column('extracted_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('ai_scorecard', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('flagged_by_ai', sa.Boolean(), nullable=True),
    sa.Column('reason_for_flag', sa.String(length=255), nullable=True),
    sa.Column('gar_context_reference', sa.String(length=100), nullable=True),
    sa.Column('gar_notes', sa.Text(), nullable=True),
    sa.Column('context_tags', sa.ARRAY(sa.String(length=50)), nullable=True),
    sa.Column('role_visibility', sa.ARRAY(sa.String(length=50)), nullable=True),
    sa.Column('external_reference', sa.String(length=100), nullable=True),
    sa.Column('external_system', sa.String(length=100), nullable=True),
    sa.Column('sync_status', sa.String(length=50), nullable=True),
    sa.Column('last_synced_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('creditors', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_creditors_company_name'), ['company_name'], unique=False)
        batch_op.create_index(batch_op.f('ix_creditors_registration_number'), ['registration_number'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('creditors', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_creditors_registration_number'))
        batch_op.drop_index(batch_op.f('ix_creditors_company_name'))

    op.drop_table('creditors')
    # ### end Alembic commands ###
