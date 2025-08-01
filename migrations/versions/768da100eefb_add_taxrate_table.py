"""Add TaxRate table

Revision ID: 768da100eefb
Revises: ae8bcebb0ae7
Create Date: 2025-07-14 18:48:18.366229

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '768da100eefb'
down_revision = 'ae8bcebb0ae7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tax_rates',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('rate', sa.Float(), nullable=False),
    sa.Column('tax_type', sa.String(length=50), nullable=True),
    sa.Column('country', sa.String(length=100), nullable=False),
    sa.Column('region', sa.String(length=100), nullable=True),
    sa.Column('effective_from', sa.Date(), nullable=False),
    sa.Column('effective_to', sa.Date(), nullable=True),
    sa.Column('ai_classification', sa.String(length=255), nullable=True),
    sa.Column('parsed_summary', sa.Text(), nullable=True),
    sa.Column('gar_context_reference', sa.String(length=100), nullable=True),
    sa.Column('flagged_by_ai', sa.Boolean(), nullable=True),
    sa.Column('gar_notes', sa.Text(), nullable=True),
    sa.Column('gar_score', sa.Float(), nullable=True),
    sa.Column('gar_decision_reason', sa.Text(), nullable=True),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.Column('updated_by_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('user_agent', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('generated_report_logs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('config_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'financial_report_configs', ['config_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('generated_report_logs', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('config_id')

    op.drop_table('tax_rates')
    # ### end Alembic commands ###
