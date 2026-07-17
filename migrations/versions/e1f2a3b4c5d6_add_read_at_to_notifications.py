"""add read_at to notifications

Revision ID: e1f2a3b4c5d6
Revises: d8a6b3f1c2e4
Create Date: 2026-06-16 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "e1f2a3b4c5d6"
down_revision = "d8a6b3f1c2e4"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("notifications", schema=None) as batch_op:
        batch_op.add_column(sa.Column("read_at", sa.DateTime(), nullable=True))
        batch_op.create_index(batch_op.f("ix_notifications_read_at"), ["read_at"], unique=False)


def downgrade():
    with op.batch_alter_table("notifications", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_notifications_read_at"))
        batch_op.drop_column("read_at")
