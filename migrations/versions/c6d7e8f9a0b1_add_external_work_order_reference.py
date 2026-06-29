"""add external work order reference to job dockets

Revision ID: c6d7e8f9a0b1
Revises: b5e6f7a8c9d0
Create Date: 2026-06-29 13:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "c6d7e8f9a0b1"
down_revision = "b5e6f7a8c9d0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("job_dockets", schema=None) as batch_op:
        batch_op.add_column(sa.Column("external_work_order_reference", sa.String(length=120), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_job_dockets_external_work_order_reference"),
            ["external_work_order_reference"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("job_dockets", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_job_dockets_external_work_order_reference"))
        batch_op.drop_column("external_work_order_reference")
