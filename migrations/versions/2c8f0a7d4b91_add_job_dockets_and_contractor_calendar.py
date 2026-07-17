"""add job dockets and contractor calendar

Revision ID: 2c8f0a7d4b91
Revises: 1b7d9e4c6a23
Create Date: 2026-06-25 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "2c8f0a7d4b91"
down_revision = "1b7d9e4c6a23"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "job_dockets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("docket_number", sa.String(length=40), nullable=True),
        sa.Column("contractor_job_number", sa.String(length=80), nullable=True),
        sa.Column("work_order_id", sa.Integer(), nullable=False),
        sa.Column("contractor_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column("assigned_engineer_id", sa.Integer(), nullable=True),
        sa.Column("assigned_engineer_ids", sa.JSON(), nullable=True),
        sa.Column("assigned_team_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=80), nullable=False, server_default="Accepted - Awaiting Scheduling"),
        sa.Column("priority", sa.String(length=50), nullable=True),
        sa.Column("required_trade", sa.String(length=100), nullable=True),
        sa.Column("scope_of_works", sa.Text(), nullable=True),
        sa.Column("access_notes", sa.Text(), nullable=True),
        sa.Column("contact_name", sa.String(length=120), nullable=True),
        sa.Column("contact_phone", sa.String(length=50), nullable=True),
        sa.Column("contact_email", sa.String(length=120), nullable=True),
        sa.Column("scheduled_date", sa.Date(), nullable=True),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("scheduling_notes", sa.Text(), nullable=True),
        sa.Column("completion_date", sa.DateTime(), nullable=True),
        sa.Column("chargeable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("quotation_reference", sa.String(length=100), nullable=True),
        sa.Column("purchase_order_number", sa.String(length=100), nullable=True),
        sa.Column("invoice_status", sa.String(length=50), nullable=False, server_default="Not Ready"),
        sa.Column("payment_status", sa.String(length=50), nullable=False, server_default="Not Invoiced"),
        sa.Column("source_module", sa.String(length=80), nullable=False, server_default="Contractor Logix"),
        sa.Column("gar_chat_ready", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assigned_engineer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["assigned_team_id"], ["contractor_teams.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["contractor_id"], ["contractors.id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"]),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("docket_number"),
        sa.UniqueConstraint("work_order_id"),
    )
    with op.batch_alter_table("job_dockets", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_job_dockets_assigned_engineer_id"), ["assigned_engineer_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_job_dockets_assigned_team_id"), ["assigned_team_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_job_dockets_client_id"), ["client_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_job_dockets_company_id"), ["company_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_job_dockets_contractor_id"), ["contractor_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_job_dockets_docket_number"), ["docket_number"], unique=False)
        batch_op.create_index(batch_op.f("ix_job_dockets_scheduled_date"), ["scheduled_date"], unique=False)
        batch_op.create_index(batch_op.f("ix_job_dockets_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_job_dockets_unit_id"), ["unit_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_job_dockets_work_order_id"), ["work_order_id"], unique=False)

    op.create_table(
        "contractor_calendar_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_docket_id", sa.Integer(), nullable=False),
        sa.Column("work_order_id", sa.Integer(), nullable=False),
        sa.Column("contractor_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column("assigned_engineer_id", sa.Integer(), nullable=True),
        sa.Column("assigned_engineer_ids", sa.JSON(), nullable=True),
        sa.Column("assigned_team_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("calendar_status", sa.String(length=60), nullable=False, server_default="Scheduled"),
        sa.Column("priority", sa.String(length=50), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("ics_uid", sa.String(length=120), nullable=True),
        sa.Column("gar_chat_ready", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assigned_engineer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["assigned_team_id"], ["contractor_teams.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["contractor_id"], ["contractors.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["job_docket_id"], ["job_dockets.id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ics_uid"),
    )
    with op.batch_alter_table("contractor_calendar_entries", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_contractor_calendar_entries_assigned_engineer_id"), ["assigned_engineer_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_contractor_calendar_entries_assigned_team_id"), ["assigned_team_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_contractor_calendar_entries_calendar_status"), ["calendar_status"], unique=False)
        batch_op.create_index(batch_op.f("ix_contractor_calendar_entries_client_id"), ["client_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_contractor_calendar_entries_company_id"), ["company_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_contractor_calendar_entries_contractor_id"), ["contractor_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_contractor_calendar_entries_ics_uid"), ["ics_uid"], unique=False)
        batch_op.create_index(batch_op.f("ix_contractor_calendar_entries_job_docket_id"), ["job_docket_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_contractor_calendar_entries_scheduled_date"), ["scheduled_date"], unique=False)
        batch_op.create_index(batch_op.f("ix_contractor_calendar_entries_unit_id"), ["unit_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_contractor_calendar_entries_work_order_id"), ["work_order_id"], unique=False)
        batch_op.create_index("ix_contractor_calendar_contractor_date", ["contractor_id", "scheduled_date"], unique=False)
        batch_op.create_index("ix_contractor_calendar_engineer_date", ["assigned_engineer_id", "scheduled_date"], unique=False)


def downgrade():
    with op.batch_alter_table("contractor_calendar_entries", schema=None) as batch_op:
        batch_op.drop_index("ix_contractor_calendar_engineer_date")
        batch_op.drop_index("ix_contractor_calendar_contractor_date")
        batch_op.drop_index(batch_op.f("ix_contractor_calendar_entries_work_order_id"))
        batch_op.drop_index(batch_op.f("ix_contractor_calendar_entries_unit_id"))
        batch_op.drop_index(batch_op.f("ix_contractor_calendar_entries_scheduled_date"))
        batch_op.drop_index(batch_op.f("ix_contractor_calendar_entries_job_docket_id"))
        batch_op.drop_index(batch_op.f("ix_contractor_calendar_entries_ics_uid"))
        batch_op.drop_index(batch_op.f("ix_contractor_calendar_entries_contractor_id"))
        batch_op.drop_index(batch_op.f("ix_contractor_calendar_entries_company_id"))
        batch_op.drop_index(batch_op.f("ix_contractor_calendar_entries_client_id"))
        batch_op.drop_index(batch_op.f("ix_contractor_calendar_entries_calendar_status"))
        batch_op.drop_index(batch_op.f("ix_contractor_calendar_entries_assigned_team_id"))
        batch_op.drop_index(batch_op.f("ix_contractor_calendar_entries_assigned_engineer_id"))
    op.drop_table("contractor_calendar_entries")

    with op.batch_alter_table("job_dockets", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_job_dockets_work_order_id"))
        batch_op.drop_index(batch_op.f("ix_job_dockets_unit_id"))
        batch_op.drop_index(batch_op.f("ix_job_dockets_status"))
        batch_op.drop_index(batch_op.f("ix_job_dockets_scheduled_date"))
        batch_op.drop_index(batch_op.f("ix_job_dockets_docket_number"))
        batch_op.drop_index(batch_op.f("ix_job_dockets_contractor_id"))
        batch_op.drop_index(batch_op.f("ix_job_dockets_company_id"))
        batch_op.drop_index(batch_op.f("ix_job_dockets_client_id"))
        batch_op.drop_index(batch_op.f("ix_job_dockets_assigned_team_id"))
        batch_op.drop_index(batch_op.f("ix_job_dockets_assigned_engineer_id"))
    op.drop_table("job_dockets")
