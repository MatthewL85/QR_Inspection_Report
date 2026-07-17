"""add work order organisation connection

Revision ID: 9c3d7e8f1a2b
Revises: 8b2c1d4e5f6a
Create Date: 2026-06-27 09:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "9c3d7e8f1a2b"
down_revision = "8b2c1d4e5f6a"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("work_orders", schema=None) as batch_op:
        batch_op.add_column(sa.Column("organisation_connection_id", sa.Integer(), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_work_orders_organisation_connection_id"),
            ["organisation_connection_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_work_orders_org_connection",
            "organisation_connections",
            ["organisation_connection_id"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table("work_orders", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_work_orders_org_connection",
            type_="foreignkey",
        )
        batch_op.drop_index(batch_op.f("ix_work_orders_organisation_connection_id"))
        batch_op.drop_column("organisation_connection_id")
