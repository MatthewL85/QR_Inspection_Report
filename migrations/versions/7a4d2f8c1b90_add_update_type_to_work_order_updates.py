"""add update type to work order updates

Revision ID: 7a4d2f8c1b90
Revises: 8e5f1b3c9d02
Create Date: 2026-06-25 17:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "7a4d2f8c1b90"
down_revision = "8e5f1b3c9d02"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "work_order_progress_updates",
        sa.Column("update_type", sa.String(length=40), nullable=False, server_default="progress"),
    )
    op.alter_column("work_order_progress_updates", "update_type", server_default=None)


def downgrade():
    op.drop_column("work_order_progress_updates", "update_type")
