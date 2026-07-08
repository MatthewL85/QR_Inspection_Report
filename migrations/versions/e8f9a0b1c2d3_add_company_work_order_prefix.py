"""add company work order prefix

Revision ID: e8f9a0b1c2d3
Revises: d7e8f9a0b1c2
Create Date: 2026-07-04 08:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "e8f9a0b1c2d3"
down_revision = "d7e8f9a0b1c2"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("companies", schema=None) as batch_op:
        batch_op.add_column(sa.Column("work_order_prefix", sa.String(length=12), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_companies_work_order_prefix"),
            ["work_order_prefix"],
            unique=True,
        )


def downgrade():
    with op.batch_alter_table("companies", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_companies_work_order_prefix"))
        batch_op.drop_column("work_order_prefix")
