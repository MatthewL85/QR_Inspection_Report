"""add letting agent fields to units

Revision ID: 3b8a6c4d9e12
Revises: 2d7f3a9c5b61
Create Date: 2026-05-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "3b8a6c4d9e12"
down_revision = "2d7f3a9c5b61"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.add_column(sa.Column("letting_agent_name", sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column("letting_agent_phone", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("letting_agent_email", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("letting_agent_notes", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.drop_column("letting_agent_notes")
        batch_op.drop_column("letting_agent_email")
        batch_op.drop_column("letting_agent_phone")
        batch_op.drop_column("letting_agent_name")
