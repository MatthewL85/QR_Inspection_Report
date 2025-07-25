"""Add levy_payments table

Revision ID: d723f18f0807
Revises: 60d6d32d6a6f
Create Date: 2025-07-13 13:27:34.436665

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd723f18f0807'
down_revision = '60d6d32d6a6f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('levy_payments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('levy_id', sa.Integer(), nullable=False),
    sa.Column('unit_id', sa.Integer(), nullable=False),
    sa.Column('paid_by_id', sa.Integer(), nullable=False),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=10), nullable=True),
    sa.Column('payment_date', sa.DateTime(), nullable=True),
    sa.Column('payment_method', sa.String(length=50), nullable=True),
    sa.Column('payment_reference', sa.String(length=100), nullable=True),
    sa.Column('channel', sa.String(length=50), nullable=True),
    sa.Column('is_reversed', sa.Boolean(), nullable=True),
    sa.Column('reversal_reason', sa.Text(), nullable=True),
    sa.Column('is_verified', sa.Boolean(), nullable=True),
    sa.Column('verified_by_id', sa.Integer(), nullable=True),
    sa.Column('parsed_text', sa.Text(), nullable=True),
    sa.Column('extracted_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('ai_flagged', sa.Boolean(), nullable=True),
    sa.Column('ai_notes', sa.Text(), nullable=True),
    sa.Column('gar_context_reference', sa.String(length=100), nullable=True),
    sa.Column('synced_with_provider', sa.String(length=100), nullable=True),
    sa.Column('external_payment_id', sa.String(length=100), nullable=True),
    sa.Column('last_synced_at', sa.DateTime(), nullable=True),
    sa.Column('sync_status', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('ip_logged_from', sa.String(length=45), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['levy_id'], ['levies.id'], ),
    sa.ForeignKeyConstraint(['paid_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ),
    sa.ForeignKeyConstraint(['verified_by_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('bank_transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('service_charge_payment_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'service_charge_payments', ['service_charge_payment_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bank_transactions', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('service_charge_payment_id')

    op.drop_table('levy_payments')
    # ### end Alembic commands ###
