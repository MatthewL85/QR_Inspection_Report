"""Add delivery tracking to unit access invites

Revision ID: 0c4b8f9a2d71
Revises: f2a7c9d8e1b0
Create Date: 2026-06-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0c4b8f9a2d71"
down_revision = "f2a7c9d8e1b0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("unit_access_invites", schema=None) as batch_op:
        batch_op.add_column(sa.Column("delivery_status", sa.String(length=32), nullable=False, server_default="not_sent"))
        batch_op.add_column(sa.Column("sent_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("send_count", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("last_delivery_error", sa.Text(), nullable=True))
        batch_op.create_index(batch_op.f("ix_unit_access_invites_delivery_status"), ["delivery_status"], unique=False)


def downgrade():
    with op.batch_alter_table("unit_access_invites", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_unit_access_invites_delivery_status"))
        batch_op.drop_column("last_delivery_error")
        batch_op.drop_column("send_count")
        batch_op.drop_column("sent_at")
        batch_op.drop_column("delivery_status")
