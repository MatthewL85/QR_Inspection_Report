from datetime import date
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB

class Tenancy(db.Model):
    __tablename__ = 'tenancies'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    resident_id = db.Column(db.Integer, db.ForeignKey('residents.id'), nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 📅 Lease Metadata
    lease_start_date = db.Column(db.Date, nullable=False, default=date.today)
    lease_end_date = db.Column(db.Date, nullable=True)
    break_clause_date = db.Column(db.Date, nullable=True)

    # 💰 Rent & Charges
    rent_amount = db.Column(db.Numeric(10, 2), nullable=True)
    service_charge = db.Column(db.Numeric(10, 2), nullable=True)
    payment_frequency = db.Column(db.String(50), nullable=True)  # Monthly, Quarterly, etc.
    rent_currency = db.Column(db.String(10), default="EUR")  # ISO currency code

    # 🔒 Security & Compliance
    is_data_encrypted = db.Column(db.Boolean, default=True)  # Indicates if PII is encrypted
    is_gdpr_consented = db.Column(db.Boolean, default=False)
    gdpr_consent_date = db.Column(db.Date, nullable=True)

    # 📄 Lease Documents / API integration
    lease_document_url = db.Column(db.String(255), nullable=True)  # S3 or media path
    external_property_ref = db.Column(db.String(100), nullable=True)  # For CRM/API syncs
    external_lease_id = db.Column(db.String(100), nullable=True)

    # 🔄 Status & Management
    status = db.Column(db.String(50), nullable=False, default='Active')  # Active, Terminated, Suspended
    termination_reason = db.Column(db.String(255), nullable=True)
    auto_renew = db.Column(db.Boolean, default=False)

    # 🧠 AI & GAR Parsing Enhancements
    parsed_summary = db.Column(db.Text, nullable=True)
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)  # AI-extracted key info from lease
    gar_recommendations = db.Column(JSONB, nullable=True)  # AI-generated renewal/termination logic

    # 🧾 Audit / Change Log
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
