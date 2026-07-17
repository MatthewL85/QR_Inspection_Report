"""add standalone docket evidence fields

Revision ID: d7e8f9a0b1c2
Revises: c6d7e8f9a0b1
Create Date: 2026-06-29 18:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "d7e8f9a0b1c2"
down_revision = "c6d7e8f9a0b1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("job_dockets", schema=None) as batch_op:
        batch_op.add_column(sa.Column("evidence_links", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("attachments_count", sa.Integer(), nullable=False, server_default="0"))

    with op.batch_alter_table("job_dockets", schema=None) as batch_op:
        batch_op.alter_column("attachments_count", server_default=None)


def downgrade():
    with op.batch_alter_table("job_dockets", schema=None) as batch_op:
        batch_op.drop_column("attachments_count")
        batch_op.drop_column("evidence_links")
