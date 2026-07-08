"""add core document templates

Revision ID: a0b1c2d3e4f5
Revises: f9a0b1c2d3e4
Create Date: 2026-07-06 18:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "a0b1c2d3e4f5"
down_revision = "f9a0b1c2d3e4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "core_document_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("module_key", sa.String(length=80), nullable=False),
        sa.Column("document_type", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("version_label", sa.String(length=40), nullable=False),
        sa.Column("template_format", sa.String(length=40), nullable=False),
        sa.Column("html_body", sa.Text(), nullable=True),
        sa.Column("terms_body", sa.Text(), nullable=True),
        sa.Column("footer_body", sa.Text(), nullable=True),
        sa.Column("logo_mode", sa.String(length=40), nullable=False),
        sa.Column("primary_brand_source", sa.String(length=40), nullable=False),
        sa.Column("include_signature_block", sa.Boolean(), nullable=False),
        sa.Column("include_terms", sa.Boolean(), nullable=False),
        sa.Column("number_prefix", sa.String(length=30), nullable=True),
        sa.Column("sequence_padding", sa.Integer(), nullable=False),
        sa.Column("supported_output_formats", sa.JSON(), nullable=True),
        sa.Column("required_context_keys", sa.JSON(), nullable=True),
        sa.Column("default_context", sa.JSON(), nullable=True),
        sa.Column("visibility_scope", sa.String(length=80), nullable=False),
        sa.Column("is_locked", sa.Boolean(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id",
            "module_key",
            "document_type",
            "version_label",
            name="uq_core_document_template_scope_version",
        ),
    )
    with op.batch_alter_table("core_document_templates", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_core_document_templates_company_id"), ["company_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_core_document_templates_created_by_id"), ["created_by_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_core_document_templates_document_type"), ["document_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_core_document_templates_module_key"), ["module_key"], unique=False)
        batch_op.create_index(batch_op.f("ix_core_document_templates_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_core_document_templates_updated_by_id"), ["updated_by_id"], unique=False)


def downgrade():
    with op.batch_alter_table("core_document_templates", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_core_document_templates_updated_by_id"))
        batch_op.drop_index(batch_op.f("ix_core_document_templates_status"))
        batch_op.drop_index(batch_op.f("ix_core_document_templates_module_key"))
        batch_op.drop_index(batch_op.f("ix_core_document_templates_document_type"))
        batch_op.drop_index(batch_op.f("ix_core_document_templates_created_by_id"))
        batch_op.drop_index(batch_op.f("ix_core_document_templates_company_id"))
    op.drop_table("core_document_templates")
