"""add contract_audits

Revision ID: 0c078bd4992c
Revises: 960863140817
Create Date: 2025-09-07 13:51:59.785608

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0c078bd4992c'
down_revision = '960863140817'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'contract_audits',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('contract_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=32), nullable=False),  # create | update | renew | delete | bootstrap
        sa.Column('actor_id', sa.Integer(), nullable=True),         # user who performed the action (nullable for system)
        sa.Column('happened_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('before_data', sa.JSON(), nullable=True),
        sa.Column('after_data', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
    )

    # FKs (use your actual table names if different)
    op.create_foreign_key(
        'fk_contract_audits_contract',
        source_table='contract_audits',
        referent_table='contracts',           # <-- change if your contracts table is named differently
        local_cols=['contract_id'],
        remote_cols=['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_contract_audits_actor',
        source_table='contract_audits',
        referent_table='users',               # <-- change if your users table is named differently
        local_cols=['actor_id'],
        remote_cols=['id'],
        ondelete='SET NULL'
    )

    # Helpful indexes
    op.create_index('ix_contract_audits_contract_id', 'contract_audits', ['contract_id'])
    op.create_index('ix_contract_audits_happened_at', 'contract_audits', ['happened_at'])
    op.create_index('ix_contract_audits_action', 'contract_audits', ['action'])
    op.create_index('ix_contract_audits_actor_id', 'contract_audits', ['actor_id'])

def downgrade():
    op.drop_index('ix_contract_audits_actor_id', table_name='contract_audits')
    op.drop_index('ix_contract_audits_action', table_name='contract_audits')
    op.drop_index('ix_contract_audits_happened_at', table_name='contract_audits')
    op.drop_index('ix_contract_audits_contract_id', table_name='contract_audits')
    op.drop_constraint('fk_contract_audits_actor', 'contract_audits', type_='foreignkey')
    op.drop_constraint('fk_contract_audits_contract', 'contract_audits', type_='foreignkey')
    op.drop_table('contract_audits')
