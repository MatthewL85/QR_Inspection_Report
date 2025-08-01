"""Add ExternalEmailLog Table

Revision ID: ff2e428b57ca
Revises: a1f791bf7ac3
Create Date: 2025-07-17 21:35:37.967449

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ff2e428b57ca'
down_revision = 'a1f791bf7ac3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('external_email_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('message_id', sa.String(length=255), nullable=True),
    sa.Column('in_reply_to', sa.String(length=255), nullable=True),
    sa.Column('thread_id', sa.String(length=255), nullable=True),
    sa.Column('sender', sa.String(length=255), nullable=False),
    sa.Column('recipient', sa.String(length=255), nullable=False),
    sa.Column('cc', sa.Text(), nullable=True),
    sa.Column('bcc', sa.Text(), nullable=True),
    sa.Column('subject', sa.String(length=512), nullable=False),
    sa.Column('body_plain', sa.Text(), nullable=True),
    sa.Column('body_html', sa.Text(), nullable=True),
    sa.Column('received_at', sa.DateTime(), nullable=True),
    sa.Column('email_source', sa.String(length=50), nullable=True),
    sa.Column('parsed_summary', sa.Text(), nullable=True),
    sa.Column('extracted_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('parsed_keywords', sa.ARRAY(sa.String()), nullable=True),
    sa.Column('learning_signals', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('gar_context_tag', sa.String(length=100), nullable=True),
    sa.Column('gar_chat_visible', sa.Boolean(), nullable=True),
    sa.Column('related_module', sa.String(length=100), nullable=True),
    sa.Column('related_id', sa.Integer(), nullable=True),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.Column('source_ip', sa.String(length=50), nullable=True),
    sa.Column('reviewed_by_id', sa.Integer(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(), nullable=True),
    sa.Column('is_flagged', sa.Boolean(), nullable=True),
    sa.Column('flag_reason', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('message_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('external_email_logs')
    # ### end Alembic commands ###
