"""Extend ClientContract with governance + GAR/AI fields

Revision ID: b0957051253b
Revises: 23226e81973a
Create Date: 2025-09-22 20:49:15.131200

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b0957051253b'
down_revision = '23226e81973a'
branch_labels = None
depends_on = None


def upgrade():
    # 1) Add columns inside batch with safe defaults (or nullable=True)
    with op.batch_alter_table('client_contracts', schema=None) as b:
        # governance fields (all nullable, safe)
        b.add_column(sa.Column('contract_kind', sa.String(length=32), nullable=True))
        b.add_column(sa.Column('governance_level', sa.String(length=16), nullable=True))
        b.add_column(sa.Column('parent_contract_id', sa.Integer(), nullable=True))
        b.add_column(sa.Column('compliance_status', sa.String(length=16), nullable=True))
        b.add_column(sa.Column('compliance_message', sa.Text(), nullable=True))
        b.create_foreign_key(
            'fk_contract_parent', 'client_contracts',
            ['parent_contract_id'], ['id'], ondelete='SET NULL'
        )

        # GAR / AI — add as NULLABLE first (or with a server default), then tighten below
        b.add_column(sa.Column('profile_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        b.add_column(sa.Column('ai_parsed_text', sa.Text(), nullable=True))
        b.add_column(sa.Column('ai_parsed_summary', sa.Text(), nullable=True))
        b.add_column(sa.Column('ai_extracted_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        b.add_column(sa.Column('ai_scorecard', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        b.add_column(sa.Column('ai_rank', sa.Integer(), nullable=True))

        # 🔧 The troublemaker: add with a temporary server default and nullable=True
        b.add_column(sa.Column('ai_is_preferred', sa.Boolean(), nullable=True, server_default=sa.text('FALSE')))

        b.add_column(sa.Column('ai_reason_for_recommendation', sa.Text(), nullable=True))
        b.add_column(sa.Column('ai_recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        b.add_column(sa.Column('ai_notes', sa.Text(), nullable=True))
        b.add_column(sa.Column('ai_model_name', sa.String(length=128), nullable=True))
        b.add_column(sa.Column('ai_model_version', sa.String(length=64), nullable=True))
        b.add_column(sa.Column('ai_policy_version', sa.String(length=64), nullable=True))
        b.add_column(sa.Column('ai_last_parsed_at', sa.DateTime(), nullable=True))
        b.add_column(sa.Column('ai_last_scored_at', sa.DateTime(), nullable=True))
        b.add_column(sa.Column('ai_visibility', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        b.add_column(sa.Column('ai_context', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        b.add_column(sa.Column('ai_errors', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        b.add_column(sa.Column('ai_embedding', postgresql.ARRAY(sa.Float()), nullable=True))

        # legacy fields you already had are left as-is

    # 2) Backfill any NULLs to satisfy future NOT NULL constraints
    op.execute("UPDATE client_contracts SET ai_is_preferred = FALSE WHERE ai_is_preferred IS NULL;")

    # 3) Tighten constraints & drop temporary defaults outside batch (clean SQL emitted)
    op.alter_column(
        'client_contracts', 'ai_is_preferred',
        existing_type=sa.Boolean(),
        nullable=False
    )
    op.execute("ALTER TABLE client_contracts ALTER COLUMN ai_is_preferred DROP DEFAULT;")

    # 4) Optional GIN indexes (JSONB)
    op.create_index(
        "ix_client_contract_ai_extracted_gin",
        "client_contracts", ["ai_extracted_data"],
        unique=False, postgresql_using="gin"
    )
    op.create_index(
        "ix_client_contract_ai_scorecard_gin",
        "client_contracts", ["ai_scorecard"],
        unique=False, postgresql_using="gin"
    )

def downgrade():
    op.drop_index("ix_client_contract_ai_scorecard_gin", table_name="client_contracts")
    op.drop_index("ix_client_contract_ai_extracted_gin", table_name="client_contracts")
    with op.batch_alter_table('client_contracts', schema=None) as b:
        b.drop_column('ai_embedding')
        b.drop_column('ai_errors')
        b.drop_column('ai_context')
        b.drop_column('ai_visibility')
        b.drop_column('ai_last_scored_at')
        b.drop_column('ai_last_parsed_at')
        b.drop_column('ai_policy_version')
        b.drop_column('ai_model_version')
        b.drop_column('ai_model_name')
        b.drop_column('ai_notes')
        b.drop_column('ai_recommendations')
        b.drop_column('ai_reason_for_recommendation')
        b.drop_column('ai_is_preferred')
        b.drop_column('ai_rank')
        b.drop_column('ai_scorecard')
        b.drop_column('ai_extracted_data')
        b.drop_column('ai_parsed_summary')
        b.drop_column('ai_parsed_text')
        b.drop_column('profile_snapshot')
        b.drop_constraint('fk_contract_parent', type_='foreignkey')
        b.drop_column('compliance_message')
        b.drop_column('compliance_status')
        b.drop_column('parent_contract_id')
        b.drop_column('governance_level')
        b.drop_column('contract_kind')

