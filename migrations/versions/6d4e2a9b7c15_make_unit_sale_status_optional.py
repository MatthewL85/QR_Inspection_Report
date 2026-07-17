"""make unit sale status optional

Revision ID: 6d4e2a9b7c15
Revises: 5c2f1d7e8a94
Create Date: 2026-05-18 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "6d4e2a9b7c15"
down_revision = "5c2f1d7e8a94"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.alter_column(
            "sale_status",
            existing_type=sa.String(length=50),
            nullable=True,
            server_default=None,
        )
        batch_op.alter_column(
            "conveyancing_status",
            existing_type=sa.String(length=50),
            nullable=True,
            server_default=None,
        )


def downgrade():
    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.alter_column(
            "conveyancing_status",
            existing_type=sa.String(length=50),
            nullable=False,
            server_default="not_started",
        )
        batch_op.alter_column(
            "sale_status",
            existing_type=sa.String(length=50),
            nullable=False,
            server_default="not_for_sale",
        )
