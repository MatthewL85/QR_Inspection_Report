"""add contract templates, versions, client contracts, special projects"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250906_contracts"
down_revision = None  # <- set to your latest revision id
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "contract_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("jurisdiction", sa.String(length=16), nullable=False),
        sa.Column("authority", sa.String(length=128), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )

    op.create_table(
        "contract_template_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("contract_templates.id"), nullable=False),
        sa.Column("version_label", sa.String(length=64), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("html_template", sa.Text(), nullable=False),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("ai_clause_map", sa.Text(), nullable=True),
        sa.Column("ai_status", sa.String(length=32), server_default="Published", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_table(
        "client_contracts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("template_version_id", sa.Integer(), sa.ForeignKey("contract_template_versions.id"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("contract_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=10), server_default="EUR", nullable=False),
        sa.Column("next_fee_increase_date", sa.Date(), nullable=True),
        sa.Column("additional_fees", sa.Text(), nullable=True),
        sa.Column("generated_html_path", sa.String(length=500), nullable=True),
        sa.Column("generated_pdf_path", sa.String(length=500), nullable=True),
        sa.Column("esign_provider", sa.String(length=32), nullable=True),
        sa.Column("esign_envelope_id", sa.String(length=128), nullable=True),
        sa.Column("sign_status", sa.String(length=32), server_default="Draft", nullable=False),
        sa.Column("ai_extract", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_table(
        "client_special_projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("client_contracts.id"), nullable=True),
        sa.Column("project_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("contractor_id", sa.Integer(), sa.ForeignKey("contractors.id"), nullable=True),
        sa.Column("value", sa.Numeric(12, 2), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="Open", nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
    )

def downgrade():
    op.drop_table("client_special_projects")
    op.drop_table("client_contracts")
    op.drop_table("contract_template_versions")
    op.drop_table("contract_templates")
