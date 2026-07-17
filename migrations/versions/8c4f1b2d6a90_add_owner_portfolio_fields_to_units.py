"""add owner portfolio fields to units

Revision ID: 8c4f1b2d6a90
Revises: 7b3f2a1c9d84
Create Date: 2026-05-19 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "8c4f1b2d6a90"
down_revision = "7b3f2a1c9d84"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.add_column(sa.Column("owner_portfolio_type", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("owner_portfolio_name", sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column("owner_portfolio_reference", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("owner_portfolio_notes", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.drop_column("owner_portfolio_notes")
        batch_op.drop_column("owner_portfolio_reference")
        batch_op.drop_column("owner_portfolio_name")
        batch_op.drop_column("owner_portfolio_type")
