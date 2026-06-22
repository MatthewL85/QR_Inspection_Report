"""add feedback evidence reference

Revision ID: d8a6b3f1c2e4
Revises: c7f4a9e2b1d3
Create Date: 2026-06-09 10:42:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "d8a6b3f1c2e4"
down_revision = "c7f4a9e2b1d3"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("contractor_feedback", schema=None) as batch_op:
        batch_op.add_column(sa.Column("evidence_reference", sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table("contractor_feedback", schema=None) as batch_op:
        batch_op.drop_column("evidence_reference")
