"""add contract renewal manager fields

Revision ID: 9d2a4f7c6b81
Revises: 8c4f1b2d6a90
Create Date: 2026-05-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "9d2a4f7c6b81"
down_revision = "8c4f1b2d6a90"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("client_contracts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("renewal_month", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("annual_increase_percent", sa.Numeric(6, 2), nullable=True))
        batch_op.add_column(sa.Column("target_management_fee", sa.Numeric(12, 2), nullable=True))
        batch_op.add_column(
            sa.Column(
                "new_contract_drafted",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(sa.Column("renewal_notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("alert_owner_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("last_reviewed_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("gar_contract_risk_level", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("gar_contract_recommendation", sa.Text(), nullable=True))
        batch_op.create_foreign_key(
            "fk_client_contract_alert_owner",
            "users",
            ["alert_owner_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade():
    with op.batch_alter_table("client_contracts", schema=None) as batch_op:
        batch_op.drop_constraint("fk_client_contract_alert_owner", type_="foreignkey")
        batch_op.drop_column("gar_contract_recommendation")
        batch_op.drop_column("gar_contract_risk_level")
        batch_op.drop_column("last_reviewed_at")
        batch_op.drop_column("alert_owner_id")
        batch_op.drop_column("renewal_notes")
        batch_op.drop_column("new_contract_drafted")
        batch_op.drop_column("target_management_fee")
        batch_op.drop_column("annual_increase_percent")
        batch_op.drop_column("renewal_month")
