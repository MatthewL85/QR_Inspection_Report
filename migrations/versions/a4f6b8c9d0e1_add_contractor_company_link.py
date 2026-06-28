"""add contractor company link

Revision ID: a4f6b8c9d0e1
Revises: 9c3d7e8f1a2b
Create Date: 2026-06-27 10:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "a4f6b8c9d0e1"
down_revision = "9c3d7e8f1a2b"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("contractors", schema=None) as batch_op:
        batch_op.add_column(sa.Column("company_id", sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f("ix_contractors_company_id"), ["company_id"], unique=False)
        batch_op.create_foreign_key("fk_contractors_company", "companies", ["company_id"], ["id"])

    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE contractors AS contractor
            SET company_id = company.id
            FROM companies AS company
            WHERE contractor.company_id IS NULL
              AND lower(trim(contractor.company_name)) = lower(trim(company.name))
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE contractors AS contractor
            SET company_id = linked.company_id
            FROM (
                SELECT contractor_id, min(company_id) AS company_id
                FROM users
                WHERE contractor_id IS NOT NULL
                  AND company_id IS NOT NULL
                GROUP BY contractor_id
            ) AS linked
            WHERE contractor.company_id IS NULL
              AND contractor.id = linked.contractor_id
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE users AS app_user
            SET company_id = contractor.company_id
            FROM contractors AS contractor
            WHERE app_user.contractor_id = contractor.id
              AND app_user.company_id IS NULL
              AND contractor.company_id IS NOT NULL
            """
        )
    )


def downgrade():
    with op.batch_alter_table("contractors", schema=None) as batch_op:
        batch_op.drop_constraint("fk_contractors_company", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_contractors_company_id"))
        batch_op.drop_column("company_id")
