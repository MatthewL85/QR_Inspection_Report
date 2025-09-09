"""Add capex_profile (JSONB) and capex_status to clients

Revision ID: 240905c3898d
Revises: 20c222121c07
Create Date: 2025-08-07 22:06:47.136506

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "240905c3898d"
down_revision = "20c222121c07"
branch_labels = None
depends_on = None

def upgrade():
    # 1) Ensure capex_profile is JSONB (cast existing data)
    # If it was JSON or TEXT before, this will cast safely.
    op.alter_column(
        "clients",
        "capex_profile",
        type_=postgresql.JSONB(astext_type=sa.Text()),
        postgresql_using="capex_profile::jsonb",
        existing_type=postgresql.JSON(astext_type=sa.Text())  # if it was JSON before; safe to leave even if TEXT
    )

    # 2) Add capex_status with a server_default to backfill existing rows
    op.add_column(
        "clients",
        sa.Column("capex_status", sa.String(length=50), nullable=False, server_default="not_created"),
    )

    # 3) Optional: drop the server_default after backfill so app-level default applies
    op.alter_column("clients", "capex_status", server_default=None)


def downgrade():
    # Revert capex_status
    op.drop_column("clients", "capex_status")

    # Revert capex_profile back to JSON (if you need symmetry)
    op.alter_column(
        "clients",
        "capex_profile",
        type_=postgresql.JSON(astext_type=sa.Text()),
        postgresql_using="capex_profile::json",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
    )
