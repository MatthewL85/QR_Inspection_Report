"""create units table

Revision ID: 2072cab85217
Revises: 5c10eed65262
Create Date: 2025-07-11 13:34:07.024612

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2072cab85217'
down_revision = '5c10eed65262'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('units',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('client_id', sa.Integer(), nullable=True),
    sa.Column('unit_label', sa.String(length=50), nullable=False),
    sa.Column('unit_type', sa.String(length=50), nullable=True),
    sa.Column('address_line_1', sa.String(length=200), nullable=True),
    sa.Column('postal_code', sa.String(length=20), nullable=True),
    sa.Column('block_name', sa.String(length=100), nullable=True),
    sa.Column('floor_number', sa.String(length=50), nullable=True),
    sa.Column('square_meters', sa.Float(), nullable=True),
    sa.Column('resident_id', sa.Integer(), nullable=True),
    sa.Column('tenant_id', sa.Integer(), nullable=True),
    sa.Column('occupancy_status', sa.String(length=50), nullable=True),
    sa.Column('service_charge_scheme', sa.String(length=100), nullable=True),
    sa.Column('service_charge_percent', sa.Float(), nullable=True),
    sa.Column('financial_year_start', sa.Date(), nullable=True),
    sa.Column('financial_year_end', sa.Date(), nullable=True),
    sa.Column('currency', sa.String(length=10), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('document_filename', sa.String(length=255), nullable=True),
    sa.Column('ai_parsed_lease_terms', sa.Text(), nullable=True),
    sa.Column('ai_extracted_floorplan_info', sa.Text(), nullable=True),
    sa.Column('ai_utility_flag', sa.Text(), nullable=True),
    sa.Column('ai_summary', sa.Text(), nullable=True),
    sa.Column('ai_key_clauses', sa.JSON(), nullable=True),
    sa.Column('ai_service_charge_risks', sa.Text(), nullable=True),
    sa.Column('ai_occupancy_type', sa.String(length=50), nullable=True),
    sa.Column('ai_compliance_notes', sa.Text(), nullable=True),
    sa.Column('ai_source_type', sa.String(length=50), nullable=True),
    sa.Column('ai_confidence_score', sa.Float(), nullable=True),
    sa.Column('ai_parsed_at', sa.DateTime(), nullable=True),
    sa.Column('parsed_by_ai_version', sa.String(length=50), nullable=True),
    sa.Column('is_ai_processed', sa.Boolean(), nullable=True),
    sa.Column('ai_lease_term_risk_score', sa.Float(), nullable=True),
    sa.Column('lease_start_date', sa.Date(), nullable=True),
    sa.Column('lease_end_date', sa.Date(), nullable=True),
    sa.Column('gar_recommendations', sa.Text(), nullable=True),
    sa.Column('gar_flagged_clauses', sa.JSON(), nullable=True),
    sa.Column('gar_chat_ready', sa.Boolean(), nullable=True),
    sa.Column('gar_feedback', sa.Text(), nullable=True),
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.ForeignKeyConstraint(['resident_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('units')
    # ### end Alembic commands ###
