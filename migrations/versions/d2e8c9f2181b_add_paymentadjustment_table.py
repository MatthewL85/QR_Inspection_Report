"""Add PaymentAdjustment table

Revision ID: d2e8c9f2181b
Revises: 3395970fac55
Create Date: 2025-07-14 08:12:20.226025

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg


# revision identifiers, used by Alembic.
revision = 'd2e8c9f2181b'
down_revision = '3395970fac55'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'payment_adjustments',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('payment_id', sa.Integer, sa.ForeignKey('payments.id'), nullable=False),
        sa.Column('invoice_id', sa.Integer, sa.ForeignKey('invoices.id'), nullable=True),
        sa.Column('client_id', sa.Integer, sa.ForeignKey('clients.id'), nullable=False),
        sa.Column('adjustment_type', sa.String(50), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('reason', sa.String(255), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('adjustment_date', sa.Date, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=True),
        sa.Column('created_by_id', sa.Integer, sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by_id', sa.Integer, sa.ForeignKey('users.id'), nullable=True),
        sa.Column('is_archived', sa.Boolean, default=False),
        sa.Column('parsed_summary', sa.Text, nullable=True),
        sa.Column('parsed_text', sa.Text, nullable=True),
        sa.Column('gar_feedback', pg.JSONB, nullable=True),
        sa.Column('gar_chat_reference', sa.String(255), nullable=True),
        sa.Column('ai_tags', pg.JSONB, nullable=True),
        sa.Column('external_reference', sa.String(100), nullable=True),
        sa.Column('external_source', sa.String(100), nullable=True),
        sa.Column('synced_at', sa.DateTime, nullable=True)
    )


def downgrade():
    op.drop_table('payment_adjustments')
