"""add reopen request evidence reference

Revision ID: c7f4a9e2b1d3
Revises: b6e8f2a4c9d1
Create Date: 2026-06-09 10:08:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "c7f4a9e2b1d3"
down_revision = "b6e8f2a4c9d1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("work_order_reopen_requests", schema=None) as batch_op:
        batch_op.add_column(sa.Column("evidence_reference", sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table("work_order_reopen_requests", schema=None) as batch_op:
        batch_op.drop_column("evidence_reference")
