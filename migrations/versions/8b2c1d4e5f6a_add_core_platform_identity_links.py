"""add core platform identity links

Revision ID: 8b2c1d4e5f6a
Revises: 7a4d2f8c1b90
Create Date: 2026-06-26 18:20:00.000000
"""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "8b2c1d4e5f6a"
down_revision = "7a4d2f8c1b90"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("companies", schema=None) as batch_op:
        batch_op.add_column(sa.Column("organisation_uid", sa.String(length=36), nullable=True))

    bind = op.get_bind()
    companies = bind.execute(sa.text("SELECT id FROM companies WHERE organisation_uid IS NULL")).fetchall()
    for row in companies:
        bind.execute(
            sa.text("UPDATE companies SET organisation_uid = :organisation_uid WHERE id = :company_id"),
            {"organisation_uid": str(uuid4()), "company_id": row[0]},
        )

    with op.batch_alter_table("companies", schema=None) as batch_op:
        batch_op.alter_column("organisation_uid", existing_type=sa.String(length=36), nullable=False)
        batch_op.create_index(batch_op.f("ix_companies_organisation_uid"), ["organisation_uid"], unique=True)

    op.create_table(
        "module_subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("module_key", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="active"),
        sa.Column("plan", sa.String(length=80), nullable=True),
        sa.Column("enabled_at", sa.DateTime(), nullable=False),
        sa.Column("disabled_at", sa.DateTime(), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=True),
        sa.Column("source_module", sa.String(length=80), nullable=False, server_default="Core Platform"),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "module_key", name="uq_module_subscription_company_module"),
    )
    with op.batch_alter_table("module_subscriptions", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_module_subscriptions_company_id"), ["company_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_module_subscriptions_module_key"), ["module_key"], unique=False)
        batch_op.create_index(batch_op.f("ix_module_subscriptions_status"), ["status"], unique=False)

    op.create_table(
        "organisation_connection_invites",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invite_code", sa.String(length=32), nullable=False),
        sa.Column("source_company_id", sa.Integer(), nullable=False),
        sa.Column("target_company_id", sa.Integer(), nullable=True),
        sa.Column("target_email", sa.String(length=255), nullable=True),
        sa.Column("connection_type", sa.String(length=80), nullable=False, server_default="management_contractor"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("allowed_modules_json", sa.JSON(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("accepted_by_user_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["accepted_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["source_company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["target_company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invite_code"),
    )
    with op.batch_alter_table("organisation_connection_invites", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_organisation_connection_invites_connection_type"), ["connection_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_organisation_connection_invites_expires_at"), ["expires_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_organisation_connection_invites_invite_code"), ["invite_code"], unique=True)
        batch_op.create_index(batch_op.f("ix_organisation_connection_invites_source_company_id"), ["source_company_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_organisation_connection_invites_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_organisation_connection_invites_target_company_id"), ["target_company_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_organisation_connection_invites_target_email"), ["target_email"], unique=False)

    op.create_table(
        "organisation_connections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_company_id", sa.Integer(), nullable=False),
        sa.Column("target_company_id", sa.Integer(), nullable=False),
        sa.Column("connection_type", sa.String(length=80), nullable=False, server_default="management_contractor"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="active"),
        sa.Column("source_invite_id", sa.Integer(), nullable=True),
        sa.Column("permissions_json", sa.JSON(), nullable=True),
        sa.Column("gar_visibility_scope", sa.String(length=120), nullable=False, server_default="connected_records_only"),
        sa.Column("accepted_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("accepted_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["accepted_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["source_company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["source_invite_id"], ["organisation_connection_invites.id"]),
        sa.ForeignKeyConstraint(["target_company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_company_id", "target_company_id", "connection_type", name="uq_organisation_connection_pair_type"),
    )
    with op.batch_alter_table("organisation_connections", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_organisation_connections_connection_type"), ["connection_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_organisation_connections_source_company_id"), ["source_company_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_organisation_connections_source_invite_id"), ["source_invite_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_organisation_connections_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_organisation_connections_target_company_id"), ["target_company_id"], unique=False)


def downgrade():
    with op.batch_alter_table("organisation_connections", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_organisation_connections_target_company_id"))
        batch_op.drop_index(batch_op.f("ix_organisation_connections_status"))
        batch_op.drop_index(batch_op.f("ix_organisation_connections_source_invite_id"))
        batch_op.drop_index(batch_op.f("ix_organisation_connections_source_company_id"))
        batch_op.drop_index(batch_op.f("ix_organisation_connections_connection_type"))
    op.drop_table("organisation_connections")

    with op.batch_alter_table("organisation_connection_invites", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_organisation_connection_invites_target_email"))
        batch_op.drop_index(batch_op.f("ix_organisation_connection_invites_target_company_id"))
        batch_op.drop_index(batch_op.f("ix_organisation_connection_invites_status"))
        batch_op.drop_index(batch_op.f("ix_organisation_connection_invites_source_company_id"))
        batch_op.drop_index(batch_op.f("ix_organisation_connection_invites_invite_code"))
        batch_op.drop_index(batch_op.f("ix_organisation_connection_invites_expires_at"))
        batch_op.drop_index(batch_op.f("ix_organisation_connection_invites_connection_type"))
    op.drop_table("organisation_connection_invites")

    with op.batch_alter_table("module_subscriptions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_module_subscriptions_status"))
        batch_op.drop_index(batch_op.f("ix_module_subscriptions_module_key"))
        batch_op.drop_index(batch_op.f("ix_module_subscriptions_company_id"))
    op.drop_table("module_subscriptions")

    with op.batch_alter_table("companies", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_companies_organisation_uid"))
        batch_op.drop_column("organisation_uid")
