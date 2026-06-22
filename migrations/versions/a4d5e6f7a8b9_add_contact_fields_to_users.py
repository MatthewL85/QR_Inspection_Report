"""add contact fields to users

Revision ID: a4d5e6f7a8b9
Revises: 9d2a4f7c6b81
Create Date: 2026-05-23 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "a4d5e6f7a8b9"
down_revision = "9d2a4f7c6b81"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("mobile_phone", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("direct_phone", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("phone_extension", sa.String(length=20), nullable=True))


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("phone_extension")
        batch_op.drop_column("direct_phone")
        batch_op.drop_column("mobile_phone")
