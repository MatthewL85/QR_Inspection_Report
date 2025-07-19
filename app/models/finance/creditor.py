from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class Creditor(db.Model):
    __tablename__ = 'creditors'

    id = db.Column(db.Integer, primary_key=True)

    # 🏢 Basic Info
    company_name = db.Column(db.String(255), nullable=False, index=True)
    registration_number = db.Column(db.String(100), nullable=True, index=True)
    vat_number = db.Column(db.String(100), nullable=True)
    business_type = db.Column(db.String(100), nullable=True)  # e.g. Plumbing, Electrical

    # 📞 Contact Info
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    contact_name = db.Column(db.String(150), nullable=True)
    address = db.Column(db.Text, nullable=True)

    # 💰 Finance & Accounts
    default_currency = db.Column(db.String(10), default='EUR')
    account_reference = db.Column(db.String(100), nullable=True)
    payment_terms = db.Column(db.String(100), default='30 days')

    # 📎 Compliance Documents
    contract_document = db.Column(db.String(255), nullable=True)  # Link to contract PDF
    insurance_expiry = db.Column(db.Date, nullable=True)
    health_safety_expiry = db.Column(db.Date, nullable=True)

    # 🔐 Audit Trail
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 🤖 AI / GAR Integration
    parsed_summary = db.Column(db.Text, nullable=True)
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)
    flagged_by_ai = db.Column(db.Boolean, default=False)
    reason_for_flag = db.Column(db.String(255), nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    gar_notes = db.Column(db.Text, nullable=True)
    context_tags = db.Column(db.ARRAY(db.String(50)), nullable=True)
    role_visibility = db.Column(db.ARRAY(db.String(50)), nullable=True)

    # 🔌 3rd-Party Integration
    external_reference = db.Column(db.String(100), nullable=True)
    external_system = db.Column(db.String(100), nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')  # Synced, Failed, Manual
    last_synced_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Creditor {self.company_name}>"
