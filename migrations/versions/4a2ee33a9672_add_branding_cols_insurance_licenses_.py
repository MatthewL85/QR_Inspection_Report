"""Add branding cols + insurance, licenses, emergency tables

Revision ID: 4a2ee33a9672
Revises: d5dc007ae5e5
Create Date: 2025-09-19 12:25:47.853481
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "4a2ee33a9672"
down_revision = "d5dc007ae5e5"
branch_labels = None
depends_on = None

# ---------- Define PostgreSQL ENUM types (prevent auto-create on column bind) ----------
owner_enum = postgresql.ENUM(
    "company", "client", "omc", "contractor",
    name="bank_owner_type_enum",
    create_type=False,
)
ins_enum = postgresql.ENUM(
    "Public Liability", "Employers Liability", "Professional Indemnity", "Contractors All Risks",
    name="insurance_policy_type_enum",
    create_type=False,
)
lic_status = postgresql.ENUM(
    "active", "suspended", "expired", "pending",
    name="company_license_status_enum",
    create_type=False,
)
emerg_cov = postgresql.ENUM(
    "24x7", "weeknights", "weekends", "holidays", "custom",
    name="emergency_coverage_type_enum",
    create_type=False,
)


def upgrade():
    bind = op.get_bind()

    # ---------- Create ENUM types first (idempotent) ----------
    owner_enum.create(bind, checkfirst=True)
    ins_enum.create(bind, checkfirst=True)
    lic_status.create(bind, checkfirst=True)
    emerg_cov.create(bind, checkfirst=True)

    # ---------- company_licenses ----------
    op.create_table(
        "company_licenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("country", sa.String(length=100), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("regulator_name", sa.String(length=255), nullable=False),
        sa.Column("license_type", sa.String(length=120), nullable=True),
        sa.Column("license_number", sa.String(length=120), nullable=False),
        sa.Column("scope_json", sa.Text(), nullable=True),
        sa.Column("status", lic_status, nullable=False, server_default="active"),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("document_path", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    with op.batch_alter_table("company_licenses") as batch_op:
        batch_op.create_index(batch_op.f("ix_company_licenses_company_id"), ["company_id"], unique=False)
        batch_op.create_index("ix_company_licenses_company_loc", ["company_id", "country", "region"], unique=False)
        batch_op.create_index(batch_op.f("ix_company_licenses_expiry_date"), ["expiry_date"], unique=False)

    # ---------- emergency_contacts ----------
    op.create_table(
        "emergency_contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("provider", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=False),
        sa.Column("alt_phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("service_type", sa.String(length=120), nullable=True),
        sa.Column("coverage", emerg_cov, nullable=False, server_default="custom"),
        sa.Column("days_of_week", sa.String(length=20), nullable=True),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    with op.batch_alter_table("emergency_contacts") as batch_op:
        batch_op.create_index(batch_op.f("ix_emergency_contacts_company_id"), ["company_id"], unique=False)
        batch_op.create_index("ix_emergency_contacts_company_service", ["company_id", "service_type"], unique=False)

    # ---------- insurance_policies ----------
    op.create_table(
        "insurance_policies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("policy_type", ins_enum, nullable=False),
        sa.Column("provider", sa.String(length=255), nullable=True),
        sa.Column("policy_number", sa.String(length=100), nullable=True),
        sa.Column("coverage_amount", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("document_path", sa.String(length=255), nullable=True),
        sa.Column("document_mime", sa.String(length=100), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    with op.batch_alter_table("insurance_policies") as batch_op:
        batch_op.create_index("ix_ins_policies_company_type", ["company_id", "policy_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_insurance_policies_company_id"), ["company_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_insurance_policies_expiry_date"), ["expiry_date"], unique=False)
        batch_op.create_index(batch_op.f("ix_insurance_policies_policy_number"), ["policy_number"], unique=False)
        batch_op.create_index(batch_op.f("ix_insurance_policies_policy_type"), ["policy_type"], unique=False)

    # ---------- bank_accounts (add polymorphic owner safely) ----------
    # 1) add as NULLABLE first so we can backfill
    with op.batch_alter_table("bank_accounts") as batch_op:
        batch_op.add_column(sa.Column("owner_type", owner_enum, nullable=True))
        batch_op.add_column(sa.Column("owner_id", sa.Integer(), nullable=True))
        # keep legacy company_id present (nullable) to avoid data loss
        try:
            batch_op.add_column(sa.Column("company_id", sa.Integer(), nullable=True))
        except Exception:
            pass
        batch_op.add_column(sa.Column("nickname", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("bic_swift", sa.String(length=11), nullable=True))
        batch_op.add_column(sa.Column("remittance_email", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("active", sa.Boolean(), nullable=True, server_default=sa.text("true")))
        batch_op.add_column(sa.Column("is_default", sa.Boolean(), nullable=True, server_default=sa.text("false")))

        batch_op.alter_column("account_name", type_=sa.String(length=255), existing_nullable=True)
        batch_op.alter_column("bank_name", type_=sa.String(length=255), existing_nullable=True)
        batch_op.alter_column("iban", type_=sa.String(length=34), existing_nullable=True)
        batch_op.alter_column("account_type", existing_type=sa.VARCHAR(length=50), nullable=True)
        batch_op.alter_column("created_at", existing_type=postgresql.TIMESTAMP(), nullable=True)

    # 2) backfill from legacy company_id
    op.execute(
        """
        UPDATE bank_accounts
           SET owner_type = 'company',
               owner_id   = COALESCE(company_id, 0)
         WHERE owner_type IS NULL OR owner_id IS NULL
        """
    )

    # 3) now enforce NOT NULL on owner fields and created_at
    with op.batch_alter_table("bank_accounts") as batch_op:
        batch_op.alter_column("owner_type", nullable=False, existing_type=owner_enum)
        batch_op.alter_column("owner_id", nullable=False, existing_type=sa.Integer())
        batch_op.alter_column("active", nullable=False, existing_type=sa.Boolean(), server_default=None)
        batch_op.alter_column("is_default", nullable=False, existing_type=sa.Boolean(), server_default=None)
        batch_op.alter_column("created_at", nullable=False, existing_type=postgresql.TIMESTAMP())

    # 4) indexes + partial unique (one default per owner)
    try:
        op.create_index("ix_bank_accounts_owner", "bank_accounts", ["owner_type", "owner_id"])
    except Exception:
        pass
    try:
        op.create_index(
            "uq_bank_accounts_one_default_per_owner",
            "bank_accounts",
            ["owner_type", "owner_id"],
            unique=True,
            postgresql_where=text("is_default = TRUE"),
        )
    except Exception:
        pass

    # 5) clean up legacy FKs and create FK to companies for company_id (nullable)
    with op.batch_alter_table("bank_accounts") as batch_op:
        try:
            batch_op.drop_constraint("bank_accounts_client_id_fkey", type_="foreignkey")
        except Exception:
            pass
        try:
            batch_op.drop_constraint("bank_accounts_created_by_id_fkey", type_="foreignkey")
        except Exception:
            pass
        try:
            batch_op.create_foreign_key(None, "companies", ["company_id"], ["id"], ondelete="SET NULL")
        except Exception:
            pass

        # optional: drop legacy/no-longer-used columns (only if they exist)
        for col in [
            "encryption_reference",
            "banking_provider",
            "sync_status",
            "parsed_summary",
            "current_balance",
            "ai_recommendation",
            "extracted_data",
            "ai_risk_score",
            "created_by_id",
            "flagged_by_gar",
            "access_revoked",
            "last_synced_at",
            "gar_notes",
            "gar_context_reference",
            "audit_consent_reference",
            "is_live_linked",
            "bic",
            "is_gar_verified",
            "client_id",
            "account_number_masked",
            "gar_feedback",
            "opening_balance",
            "gar_chat_ready",
        ]:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass

    # ---------- companies (branding + microsite; make booleans safe) ----------
    with op.batch_alter_table("companies") as batch_op:
        batch_op.add_column(sa.Column("brand_primary_color", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("brand_secondary_color", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("is_public_profile_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        batch_op.add_column(sa.Column("public_slug", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("public_about_md", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("public_services_json", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("public_show_contact_form", sa.Boolean(), nullable=False, server_default=sa.text("true")))
        batch_op.create_index(batch_op.f("ix_companies_public_slug"), ["public_slug"], unique=True)

    # drop server defaults we only needed for backfill
    with op.batch_alter_table("companies") as batch_op:
        batch_op.alter_column("is_public_profile_enabled", server_default=None)
        batch_op.alter_column("public_show_contact_form", server_default=None)

    # ---------- contract_audits extras ----------
    with op.batch_alter_table("contract_audits") as batch_op:
        batch_op.add_column(sa.Column("happened_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
        batch_op.add_column(sa.Column("before_data", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("after_data", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("change_set", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("parsed_summary", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("parsed_text", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("extracted_data", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("ai_scorecard", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("ai_rank", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("is_ai_preferred", sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column("reason_for_recommendation", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
        batch_op.alter_column("created_at", type_=sa.DateTime(timezone=True), existing_nullable=False)
        batch_op.create_index("ix_contract_audits_contract_happened_at", ["contract_id", "happened_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_contract_audits_happened_at"), ["happened_at"], unique=False)


def downgrade():
    # ---------- contract_audits ----------
    with op.batch_alter_table("contract_audits") as batch_op:
        batch_op.drop_index(batch_op.f("ix_contract_audits_happened_at"))
        batch_op.drop_index("ix_contract_audits_contract_happened_at")
        batch_op.alter_column("created_at", type_=postgresql.TIMESTAMP(), existing_nullable=False)
        for col in [
            "updated_at",
            "reason_for_recommendation",
            "is_ai_preferred",
            "ai_rank",
            "ai_scorecard",
            "extracted_data",
            "parsed_text",
            "parsed_summary",
            "notes",
            "change_set",
            "after_data",
            "before_data",
            "happened_at",
        ]:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass

    # ---------- companies ----------
    with op.batch_alter_table("companies") as batch_op:
        try:
            batch_op.drop_index(batch_op.f("ix_companies_public_slug"))
        except Exception:
            pass
        for col in [
            "public_show_contact_form",
            "public_services_json",
            "public_about_md",
            "public_slug",
            "is_public_profile_enabled",
            "brand_secondary_color",
            "brand_primary_color",
        ]:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass

    # ---------- bank_accounts ----------
    try:
        op.drop_index("uq_bank_accounts_one_default_per_owner", table_name="bank_accounts")
    except Exception:
        pass
    try:
        op.drop_index("ix_bank_accounts_owner", table_name="bank_accounts")
    except Exception:
        pass

    with op.batch_alter_table("bank_accounts") as batch_op:
        for col in ["owner_type", "owner_id", "active", "is_default", "created_at"]:
            try:
                batch_op.alter_column(col, nullable=True)
            except Exception:
                pass

        for col in [
            "owner_id",
            "owner_type",
            "company_id",
            "nickname",
            "bic_swift",
            "remittance_email",
            "active",
            "is_default",
        ]:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass

        try:
            batch_op.alter_column("iban", type_=sa.VARCHAR(length=50), existing_nullable=True)
        except Exception:
            pass
        try:
            batch_op.alter_column("bank_name", type_=sa.VARCHAR(length=100), existing_nullable=True)
        except Exception:
            pass
        try:
            batch_op.alter_column("account_name", type_=sa.VARCHAR(length=100), existing_nullable=False)
        except Exception:
            pass
        try:
            batch_op.alter_column("account_type", existing_type=sa.VARCHAR(length=50), nullable=False)
        except Exception:
            pass
        try:
            batch_op.alter_column("created_at", existing_type=postgresql.TIMESTAMP(), nullable=True)
        except Exception:
            pass

    # ---------- insurance_policies ----------
    with op.batch_alter_table("insurance_policies") as batch_op:
        for ix in [
            batch_op.f("ix_insurance_policies_policy_type"),
            batch_op.f("ix_insurance_policies_policy_number"),
            batch_op.f("ix_insurance_policies_expiry_date"),
            batch_op.f("ix_insurance_policies_company_id"),
            "ix_ins_policies_company_type",
        ]:
            try:
                batch_op.drop_index(ix)
            except Exception:
                pass
    op.drop_table("insurance_policies")

    # ---------- emergency_contacts ----------
    with op.batch_alter_table("emergency_contacts") as batch_op:
        for ix in [
            "ix_emergency_contacts_company_service",
            batch_op.f("ix_emergency_contacts_company_id"),
        ]:
            try:
                batch_op.drop_index(ix)
            except Exception:
                pass
    op.drop_table("emergency_contacts")

    # ---------- company_licenses ----------
    with op.batch_alter_table("company_licenses") as batch_op:
        for ix in [
            batch_op.f("ix_company_licenses_expiry_date"),
            "ix_company_licenses_company_loc",
            batch_op.f("ix_company_licenses_company_id"),
        ]:
            try:
                batch_op.drop_index(ix)
            except Exception:
                pass
    op.drop_table("company_licenses")

    # ---------- Drop ENUMs (only if no remaining dependencies) ----------
    for enum_obj in (emerg_cov, lic_status, ins_enum, owner_enum):
        try:
            enum_obj.drop(op.get_bind(), checkfirst=True)
        except Exception:
            pass
