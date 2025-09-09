"""Add onboarding flags, tenant status, subdomain & plan to companies

Revision ID: afef36adf566
Revises: 1664c870e39e
Create Date: 2025-08-14 08:41:47.300738

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'afef36adf566'
down_revision = '1664c870e39e'
branch_labels = None
depends_on = None


from alembic import op
import sqlalchemy as sa

def upgrade():
    # 1) add with server defaults so existing rows get values
    op.add_column(
        'companies',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true'))
    )
    op.add_column(
        'companies',
        sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default=sa.text('false'))
    )
    op.add_column(
        'companies',
        sa.Column('subdomain', sa.String(length=100), nullable=True)
    )
    op.add_column(
        'companies',
        sa.Column('plan', sa.String(length=50), nullable=True, server_default='trial')
    )
    op.create_index('ix_companies_subdomain', 'companies', ['subdomain'], unique=True)

    # 2) (optional) drop defaults so future inserts must set values themselves
    op.alter_column('companies', 'is_active', server_default=None)
    op.alter_column('companies', 'onboarding_completed', server_default=None)
    op.alter_column('companies', 'plan', server_default=None)

def downgrade():
    op.add_column('companies', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')))
    op.add_column('companies', sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('companies', sa.Column('subdomain', sa.String(length=100), nullable=True))
    op.add_column('companies', sa.Column('plan', sa.String(length=50), nullable=True, server_default='trial'))
    op.create_index('ix_companies_subdomain', 'companies', ['subdomain'], unique=True)

