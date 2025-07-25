"""Add ProfileChangeLog table

Revision ID: 721f3e209c5d
Revises: 062ae58f853b
Create Date: 2025-07-13 10:38:47.008818

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '721f3e209c5d'
down_revision = '062ae58f853b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('profile_change_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('changed_by', sa.Integer(), nullable=True),
    sa.Column('field_name', sa.String(length=100), nullable=False),
    sa.Column('old_value', sa.String(length=255), nullable=True),
    sa.Column('new_value', sa.String(length=255), nullable=True),
    sa.Column('change_reason', sa.Text(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('parsed_summary', sa.Text(), nullable=True),
    sa.Column('gar_flagged_risks', sa.Text(), nullable=True),
    sa.Column('gar_priority_score', sa.Float(), nullable=True),
    sa.Column('gar_chat_ready', sa.Boolean(), nullable=True),
    sa.Column('gar_feedback', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('profile_change_logs')
    # ### end Alembic commands ###
