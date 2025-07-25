"""Add Budget table

Revision ID: 1221d2a92dde
Revises: e571f2a72acd
Create Date: 2025-07-14 08:57:53.995186

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1221d2a92dde'
down_revision = 'e571f2a72acd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('budgets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fiscal_year', sa.String(length=9), nullable=False),
    sa.Column('period_start', sa.Date(), nullable=False),
    sa.Column('period_end', sa.Date(), nullable=False),
    sa.Column('client_id', sa.Integer(), nullable=False),
    sa.Column('unit_id', sa.Integer(), nullable=True),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.Column('category', sa.String(length=150), nullable=False),
    sa.Column('department', sa.String(length=100), nullable=True),
    sa.Column('budgeted_amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('actual_amount', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('variance', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('ai_flagged', sa.Boolean(), nullable=True),
    sa.Column('ai_summary', sa.Text(), nullable=True),
    sa.Column('gar_score', sa.Float(), nullable=True),
    sa.Column('ai_recommendation', sa.Text(), nullable=True),
    sa.Column('gar_alerts', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('ai_insights', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('ai_scorecard', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('flagged_by_gar', sa.Boolean(), nullable=True),
    sa.Column('gar_context_reference', sa.String(length=255), nullable=True),
    sa.Column('gar_chat_ready', sa.Boolean(), nullable=True),
    sa.Column('gar_feedback', sa.Text(), nullable=True),
    sa.Column('external_reference', sa.String(length=100), nullable=True),
    sa.Column('sync_status', sa.String(length=50), nullable=True),
    sa.Column('last_synced_at', sa.DateTime(), nullable=True),
    sa.Column('visibility_roles', sa.ARRAY(sa.String(length=50)), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('budgets')
    # ### end Alembic commands ###
