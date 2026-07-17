"""Add unit UID and member access invites

Revision ID: f2a7c9d8e1b0
Revises: e1f2a3b4c5d6
Create Date: 2026-06-19 20:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
import uuid


revision = "f2a7c9d8e1b0"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.add_column(sa.Column("unit_uid", sa.String(length=36), nullable=True))

    bind = op.get_bind()
    units = bind.execute(sa.text("SELECT id FROM units WHERE unit_uid IS NULL OR unit_uid = ''")).fetchall()
    for row in units:
        bind.execute(
            sa.text("UPDATE units SET unit_uid = :unit_uid WHERE id = :id"),
            {"unit_uid": str(uuid.uuid4()), "id": row[0]},
        )

    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.alter_column("unit_uid", existing_type=sa.String(length=36), nullable=False)
        batch_op.create_index(batch_op.f("ix_units_unit_uid"), ["unit_uid"], unique=True)

    with op.batch_alter_table("unit_memberships", schema=None) as batch_op:
        batch_op.add_column(sa.Column("client_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("status", sa.String(length=32), nullable=False, server_default="active"))
        batch_op.add_column(sa.Column("access_start", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("access_end", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("verified_at", sa.DateTime(), nullable=True))
        batch_op.create_index(batch_op.f("ix_unit_memberships_client_id"), ["client_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_unit_memberships_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_unit_memberships_user_id"), ["user_id"], unique=False)
        batch_op.create_foreign_key("fk_unit_memberships_client_id", "clients", ["client_id"], ["id"])
        batch_op.create_foreign_key("fk_unit_memberships_user_id", "users", ["user_id"], ["id"])

    bind.execute(sa.text(
        """
        UPDATE unit_memberships
        SET client_id = (
            SELECT units.client_id FROM units WHERE units.id = unit_memberships.unit_id
        )
        WHERE client_id IS NULL
        """
    ))
    bind.execute(sa.text(
        """
        UPDATE unit_memberships
        SET user_id = (
            SELECT members.user_id FROM members WHERE members.id = unit_memberships.member_id
        )
        WHERE user_id IS NULL
        """
    ))

    op.create_table(
        "unit_access_invites",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("claim_code", sa.String(length=32), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("claimed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("claimed_by_member_id", sa.Integer(), nullable=True),
        sa.Column("claimed_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["claimed_by_member_id"], ["members.id"]),
        sa.ForeignKeyConstraint(["claimed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("unit_access_invites", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_unit_access_invites_claim_code"), ["claim_code"], unique=True)
        batch_op.create_index(batch_op.f("ix_unit_access_invites_client_id"), ["client_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_unit_access_invites_company_id"), ["company_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_unit_access_invites_email"), ["email"], unique=False)
        batch_op.create_index(batch_op.f("ix_unit_access_invites_role"), ["role"], unique=False)
        batch_op.create_index(batch_op.f("ix_unit_access_invites_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_unit_access_invites_unit_id"), ["unit_id"], unique=False)


def downgrade():
    with op.batch_alter_table("unit_access_invites", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_unit_access_invites_unit_id"))
        batch_op.drop_index(batch_op.f("ix_unit_access_invites_status"))
        batch_op.drop_index(batch_op.f("ix_unit_access_invites_role"))
        batch_op.drop_index(batch_op.f("ix_unit_access_invites_email"))
        batch_op.drop_index(batch_op.f("ix_unit_access_invites_company_id"))
        batch_op.drop_index(batch_op.f("ix_unit_access_invites_client_id"))
        batch_op.drop_index(batch_op.f("ix_unit_access_invites_claim_code"))
    op.drop_table("unit_access_invites")

    with op.batch_alter_table("unit_memberships", schema=None) as batch_op:
        batch_op.drop_constraint("fk_unit_memberships_user_id", type_="foreignkey")
        batch_op.drop_constraint("fk_unit_memberships_client_id", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_unit_memberships_user_id"))
        batch_op.drop_index(batch_op.f("ix_unit_memberships_status"))
        batch_op.drop_index(batch_op.f("ix_unit_memberships_client_id"))
        batch_op.drop_column("verified_at")
        batch_op.drop_column("access_end")
        batch_op.drop_column("access_start")
        batch_op.drop_column("status")
        batch_op.drop_column("user_id")
        batch_op.drop_column("client_id")

    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_units_unit_uid"))
        batch_op.drop_column("unit_uid")
