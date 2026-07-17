"""add standalone job dockets

Revision ID: b5e6f7a8c9d0
Revises: a4f6b8c9d0e1
Create Date: 2026-06-29 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "b5e6f7a8c9d0"
down_revision = "a4f6b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("job_dockets", schema=None) as batch_op:
        batch_op.alter_column("work_order_id", existing_type=sa.Integer(), nullable=True)
        batch_op.add_column(sa.Column("instruction_source", sa.String(length=80), nullable=False, server_default="Works Logix"))
        batch_op.add_column(sa.Column("standalone_client_name", sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column("standalone_property_name", sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column("standalone_address_line_1", sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column("standalone_address_line_2", sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column("standalone_town_city", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("standalone_region", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("standalone_postal_code", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("standalone_country", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("standalone_block_name", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("standalone_core_name", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("standalone_unit_number", sa.String(length=80), nullable=True))
        batch_op.create_index(batch_op.f("ix_job_dockets_instruction_source"), ["instruction_source"], unique=False)

    with op.batch_alter_table("contractor_calendar_entries", schema=None) as batch_op:
        batch_op.alter_column("work_order_id", existing_type=sa.Integer(), nullable=True)


def downgrade():
    with op.batch_alter_table("contractor_calendar_entries", schema=None) as batch_op:
        batch_op.alter_column("work_order_id", existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table("job_dockets", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_job_dockets_instruction_source"))
        batch_op.drop_column("standalone_unit_number")
        batch_op.drop_column("standalone_core_name")
        batch_op.drop_column("standalone_block_name")
        batch_op.drop_column("standalone_country")
        batch_op.drop_column("standalone_postal_code")
        batch_op.drop_column("standalone_region")
        batch_op.drop_column("standalone_town_city")
        batch_op.drop_column("standalone_address_line_2")
        batch_op.drop_column("standalone_address_line_1")
        batch_op.drop_column("standalone_property_name")
        batch_op.drop_column("standalone_client_name")
        batch_op.drop_column("instruction_source")
        batch_op.alter_column("work_order_id", existing_type=sa.Integer(), nullable=False)
