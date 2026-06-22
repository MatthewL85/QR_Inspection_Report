"""add work order lifecycle events

Revision ID: b6e8f2a4c9d1
Revises: a4d5e6f7a8b9
Create Date: 2026-05-26 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "b6e8f2a4c9d1"
down_revision = "a4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "work_order_lifecycle_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("work_order_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column("contractor_id", sa.Integer(), nullable=True),
        sa.Column("member_id", sa.Integer(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("source_module", sa.String(length=80), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("status_snapshot", sa.String(length=50), nullable=True),
        sa.Column("actor_label", sa.String(length=160), nullable=True),
        sa.Column("visibility_scope", sa.String(length=100), nullable=False),
        sa.Column("event_metadata", sa.JSON(), nullable=True),
        sa.Column("gar_context_reference", sa.String(length=120), nullable=True),
        sa.Column("gar_chat_ready", sa.Boolean(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["contractor_id"], ["contractors.id"]),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"]),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("work_order_lifecycle_events", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_work_order_lifecycle_events_actor_user_id"), ["actor_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_work_order_lifecycle_events_client_id"), ["client_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_work_order_lifecycle_events_company_id"), ["company_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_work_order_lifecycle_events_contractor_id"), ["contractor_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_work_order_lifecycle_events_event_type"), ["event_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_work_order_lifecycle_events_member_id"), ["member_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_work_order_lifecycle_events_occurred_at"), ["occurred_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_work_order_lifecycle_events_unit_id"), ["unit_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_work_order_lifecycle_events_work_order_id"), ["work_order_id"], unique=False)
        batch_op.create_index("ix_work_order_lifecycle_work_order_occurred", ["work_order_id", "occurred_at"], unique=False)


def downgrade():
    with op.batch_alter_table("work_order_lifecycle_events", schema=None) as batch_op:
        batch_op.drop_index("ix_work_order_lifecycle_work_order_occurred")
        batch_op.drop_index(batch_op.f("ix_work_order_lifecycle_events_work_order_id"))
        batch_op.drop_index(batch_op.f("ix_work_order_lifecycle_events_unit_id"))
        batch_op.drop_index(batch_op.f("ix_work_order_lifecycle_events_occurred_at"))
        batch_op.drop_index(batch_op.f("ix_work_order_lifecycle_events_member_id"))
        batch_op.drop_index(batch_op.f("ix_work_order_lifecycle_events_event_type"))
        batch_op.drop_index(batch_op.f("ix_work_order_lifecycle_events_contractor_id"))
        batch_op.drop_index(batch_op.f("ix_work_order_lifecycle_events_company_id"))
        batch_op.drop_index(batch_op.f("ix_work_order_lifecycle_events_client_id"))
        batch_op.drop_index(batch_op.f("ix_work_order_lifecycle_events_actor_user_id"))
    op.drop_table("work_order_lifecycle_events")
