"""add sale and conveyancing status to units

Revision ID: 5c2f1d7e8a94
Revises: 4a9f2b8c7d31
Create Date: 2026-05-18 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "5c2f1d7e8a94"
down_revision = "4a9f2b8c7d31"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "sale_status",
                sa.String(length=50),
                nullable=False,
                server_default="not_for_sale",
            )
        )
        batch_op.add_column(
            sa.Column(
                "conveyancing_status",
                sa.String(length=50),
                nullable=False,
                server_default="not_started",
            )
        )


def downgrade():
    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.drop_column("conveyancing_status")
        batch_op.drop_column("sale_status")
