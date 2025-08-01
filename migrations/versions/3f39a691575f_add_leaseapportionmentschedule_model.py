"""Add LeaseApportionmentSchedule model

Revision ID: 3f39a691575f
Revises: 71dba6a584f0
Create Date: 2025-07-14 21:48:22.093811

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3f39a691575f'
down_revision = '71dba6a584f0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('lease_apportionment_schedules',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('client_id', sa.Integer(), nullable=False),
    sa.Column('unit_id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('method', sa.String(length=50), nullable=False),
    sa.Column('percentage', sa.Numeric(precision=6, scale=4), nullable=True),
    sa.Column('area_m2', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('custom_formula', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('lease_reference', sa.String(length=100), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('parsed_summary', sa.Text(), nullable=True),
    sa.Column('parsed_text', sa.Text(), nullable=True),
    sa.Column('extracted_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('ai_scorecard', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('flagged_by_gar', sa.Boolean(), nullable=True),
    sa.Column('gar_context_reference', sa.String(length=100), nullable=True),
    sa.Column('gar_notes', sa.Text(), nullable=True),
    sa.Column('context_tags', sa.ARRAY(sa.String(length=50)), nullable=True),
    sa.Column('role_visibility', sa.ARRAY(sa.String(length=50)), nullable=True),
    sa.Column('external_reference', sa.String(length=100), nullable=True),
    sa.Column('external_system', sa.String(length=100), nullable=True),
    sa.Column('sync_status', sa.String(length=50), nullable=True),
    sa.Column('last_synced_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.Column('modified_at', sa.DateTime(), nullable=True),
    sa.Column('modified_by_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['modified_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('lease_apportionment_schedules', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_lease_apportionment_schedules_client_id'), ['client_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_lease_apportionment_schedules_is_active'), ['is_active'], unique=False)
        batch_op.create_index(batch_op.f('ix_lease_apportionment_schedules_method'), ['method'], unique=False)
        batch_op.create_index(batch_op.f('ix_lease_apportionment_schedules_unit_id'), ['unit_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_lease_apportionment_schedules_year'), ['year'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('lease_apportionment_schedules', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_lease_apportionment_schedules_year'))
        batch_op.drop_index(batch_op.f('ix_lease_apportionment_schedules_unit_id'))
        batch_op.drop_index(batch_op.f('ix_lease_apportionment_schedules_method'))
        batch_op.drop_index(batch_op.f('ix_lease_apportionment_schedules_is_active'))
        batch_op.drop_index(batch_op.f('ix_lease_apportionment_schedules_client_id'))

    op.drop_table('lease_apportionment_schedules')
    # ### end Alembic commands ###
