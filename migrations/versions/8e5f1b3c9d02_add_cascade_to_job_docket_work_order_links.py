"""add cascade to job docket work order links

Revision ID: 8e5f1b3c9d02
Revises: 2c8f0a7d4b91
Create Date: 2026-06-25 12:30:00.000000
"""

from alembic import op


revision = "8e5f1b3c9d02"
down_revision = "2c8f0a7d4b91"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("job_dockets_work_order_id_fkey", "job_dockets", type_="foreignkey")
    op.create_foreign_key(
        "job_dockets_work_order_id_fkey",
        "job_dockets",
        "work_orders",
        ["work_order_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("contractor_calendar_entries_job_docket_id_fkey", "contractor_calendar_entries", type_="foreignkey")
    op.create_foreign_key(
        "contractor_calendar_entries_job_docket_id_fkey",
        "contractor_calendar_entries",
        "job_dockets",
        ["job_docket_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("contractor_calendar_entries_work_order_id_fkey", "contractor_calendar_entries", type_="foreignkey")
    op.create_foreign_key(
        "contractor_calendar_entries_work_order_id_fkey",
        "contractor_calendar_entries",
        "work_orders",
        ["work_order_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint("contractor_calendar_entries_work_order_id_fkey", "contractor_calendar_entries", type_="foreignkey")
    op.create_foreign_key(
        "contractor_calendar_entries_work_order_id_fkey",
        "contractor_calendar_entries",
        "work_orders",
        ["work_order_id"],
        ["id"],
    )

    op.drop_constraint("contractor_calendar_entries_job_docket_id_fkey", "contractor_calendar_entries", type_="foreignkey")
    op.create_foreign_key(
        "contractor_calendar_entries_job_docket_id_fkey",
        "contractor_calendar_entries",
        "job_dockets",
        ["job_docket_id"],
        ["id"],
    )

    op.drop_constraint("job_dockets_work_order_id_fkey", "job_dockets", type_="foreignkey")
    op.create_foreign_key(
        "job_dockets_work_order_id_fkey",
        "job_dockets",
        "work_orders",
        ["work_order_id"],
        ["id"],
    )
