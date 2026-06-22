"""add work order reopen requests

Revision ID: 4a9f2b8c7d31
Revises: 3b8a6c4d9e12
Create Date: 2026-05-18 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "4a9f2b8c7d31"
down_revision = "3b8a6c4d9e12"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "work_order_reopen_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("work_order_id", sa.Integer(), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=False),
        sa.Column("requested_by_member_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("additional_details", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["requested_by_member_id"], ["members.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"]),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("work_order_reopen_requests", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_work_order_reopen_requests_requested_by_member_id"), ["requested_by_member_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_work_order_reopen_requests_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_work_order_reopen_requests_unit_id"), ["unit_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_work_order_reopen_requests_work_order_id"), ["work_order_id"], unique=False)


def downgrade():
    with op.batch_alter_table("work_order_reopen_requests", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_work_order_reopen_requests_work_order_id"))
        batch_op.drop_index(batch_op.f("ix_work_order_reopen_requests_unit_id"))
        batch_op.drop_index(batch_op.f("ix_work_order_reopen_requests_status"))
        batch_op.drop_index(batch_op.f("ix_work_order_reopen_requests_requested_by_member_id"))
    op.drop_table("work_order_reopen_requests")
