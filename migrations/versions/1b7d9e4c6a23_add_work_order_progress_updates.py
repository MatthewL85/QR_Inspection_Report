"""add work order progress updates

Revision ID: 1b7d9e4c6a23
Revises: 0c4b8f9a2d71
Create Date: 2026-06-23 20:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "1b7d9e4c6a23"
down_revision = "0c4b8f9a2d71"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "work_order_progress_updates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("work_order_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column("contractor_id", sa.Integer(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("visibility_scope", sa.String(length=40), nullable=False, server_default="management"),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("evidence_links", sa.JSON(), nullable=True),
        sa.Column("attachments_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_module", sa.String(length=80), nullable=False, server_default="Contractor Logix"),
        sa.Column("gar_chat_ready", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["contractor_id"], ["contractors.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"]),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("work_order_progress_updates", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_work_order_progress_updates_client_id"), ["client_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_work_order_progress_updates_company_id"), ["company_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_work_order_progress_updates_contractor_id"), ["contractor_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_work_order_progress_updates_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_work_order_progress_updates_created_by_id"), ["created_by_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_work_order_progress_updates_unit_id"), ["unit_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_work_order_progress_updates_work_order_id"), ["work_order_id"], unique=False)
        batch_op.create_index("ix_work_order_progress_work_order_created", ["work_order_id", "created_at"], unique=False)


def downgrade():
    with op.batch_alter_table("work_order_progress_updates", schema=None) as batch_op:
        batch_op.drop_index("ix_work_order_progress_work_order_created")
        batch_op.drop_index(batch_op.f("ix_work_order_progress_updates_work_order_id"))
        batch_op.drop_index(batch_op.f("ix_work_order_progress_updates_unit_id"))
        batch_op.drop_index(batch_op.f("ix_work_order_progress_updates_created_by_id"))
        batch_op.drop_index(batch_op.f("ix_work_order_progress_updates_created_at"))
        batch_op.drop_index(batch_op.f("ix_work_order_progress_updates_contractor_id"))
        batch_op.drop_index(batch_op.f("ix_work_order_progress_updates_company_id"))
        batch_op.drop_index(batch_op.f("ix_work_order_progress_updates_client_id"))
    op.drop_table("work_order_progress_updates")
