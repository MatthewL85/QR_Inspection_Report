"""merge heads after contracts

Revision ID: d77bbcda431a
Revises: 0eab28c062bf, 20250906_contracts, 818ce89f3c18
Create Date: 2025-09-06 15:34:20.469542

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd77bbcda431a'
down_revision = ('0eab28c062bf', '20250906_contracts', '818ce89f3c18')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
