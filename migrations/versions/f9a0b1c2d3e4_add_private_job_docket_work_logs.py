"""add private job docket work logs

Revision ID: f9a0b1c2d3e4
Revises: e8f9a0b1c2d3
Create Date: 2026-07-04 09:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "f9a0b1c2d3e4"
down_revision = "e8f9a0b1c2d3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "job_docket_private_work_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_docket_id", sa.Integer(), nullable=False),
        sa.Column("contractor_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("labour_hours", sa.Numeric(8, 2), nullable=True),
        sa.Column("material_description", sa.String(length=255), nullable=True),
        sa.Column("material_quantity", sa.Numeric(10, 2), nullable=True),
        sa.Column("material_unit", sa.String(length=40), nullable=True),
        sa.Column("material_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("visibility_scope", sa.String(length=40), nullable=False, server_default="contractor_private"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["contractor_id"], ["contractors.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["job_docket_id"], ["job_dockets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("job_docket_private_work_logs", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_job_docket_private_work_logs_company_id"), ["company_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_job_docket_private_work_logs_contractor_id"), ["contractor_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_job_docket_private_work_logs_created_by_id"), ["created_by_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_job_docket_private_work_logs_job_docket_id"), ["job_docket_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_job_docket_private_work_logs_work_date"), ["work_date"], unique=False)


def downgrade():
    with op.batch_alter_table("job_docket_private_work_logs", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_job_docket_private_work_logs_work_date"))
        batch_op.drop_index(batch_op.f("ix_job_docket_private_work_logs_job_docket_id"))
        batch_op.drop_index(batch_op.f("ix_job_docket_private_work_logs_created_by_id"))
        batch_op.drop_index(batch_op.f("ix_job_docket_private_work_logs_contractor_id"))
        batch_op.drop_index(batch_op.f("ix_job_docket_private_work_logs_company_id"))
    op.drop_table("job_docket_private_work_logs")
