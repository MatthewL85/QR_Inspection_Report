"""add letting agent address fields to units

Revision ID: 7b3f2a1c9d84
Revises: 6d4e2a9b7c15
Create Date: 2026-05-19 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "7b3f2a1c9d84"
down_revision = "6d4e2a9b7c15"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.add_column(sa.Column("letting_agent_address_line1", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("letting_agent_address_line2", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("letting_agent_city", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("letting_agent_region", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("letting_agent_postcode", sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column("letting_agent_country", sa.String(length=120), nullable=True))


def downgrade():
    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.drop_column("letting_agent_country")
        batch_op.drop_column("letting_agent_postcode")
        batch_op.drop_column("letting_agent_region")
        batch_op.drop_column("letting_agent_city")
        batch_op.drop_column("letting_agent_address_line2")
        batch_op.drop_column("letting_agent_address_line1")
