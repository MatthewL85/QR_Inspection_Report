from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import validates

class LateFeeAndInterestPolicy(db.Model):
    __tablename__ = 'late_fee_interest_policies'

    id = db.Column(db.Integer, primary_key=True)

    # 🔐 Multi-Tenant Access
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False, index=True)

    # 📦 Application Scope
    applies_to = db.Column(db.String(50), nullable=False, index=True)  # e.g. 'Service Charge', 'Levy', 'Both'
    area_type_id = db.Column(db.Integer, db.ForeignKey('area_types.id'), nullable=True)

    # 💸 Fee Structure
    grace_period_days = db.Column(db.Integer, default=14)
    fixed_fee = db.Column(db.Numeric(10, 2), nullable=True)
    interest_rate_percent = db.Column(db.Float, nullable=True)
    interest_frequency = db.Column(db.String(50), default='Monthly')  # Daily, Monthly, Annually
    compound_interest = db.Column(db.Boolean, default=False)
    maximum_fee = db.Column(db.Numeric(10, 2), nullable=True)
    min_fee_trigger_amount = db.Column(db.Numeric(10, 2), default=0.00)

    # 📄 Lease Reference
    lease_clause_reference = db.Column(db.String(100), nullable=True)
    lease_clause_text = db.Column(db.Text, nullable=True)

    # 🤖 AI / GAR Enhancements
    parsed_summary = db.Column(db.Text, nullable=True)
    parsed_text = db.Column(db.Text, nullable=True)
    ai_tags = db.Column(db.Text, nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    gar_risk_flag = db.Column(db.Boolean, default=False)
    context_tags = db.Column(db.ARRAY(db.String(50)), nullable=True)
    role_visibility = db.Column(db.ARRAY(db.String(50)), nullable=True)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🔌 3rd-Party Integration
    external_reference = db.Column(db.String(100), nullable=True)
    external_system = db.Column(db.String(100), nullable=True)     # e.g. Yardi, MRI
    sync_status = db.Column(db.String(50), default='Pending')      # Synced, Failed, Manual
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # ⏱ Meta
    effective_date = db.Column(db.Date, nullable=False, default=datetime.utcnow, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # 🔗 Relationships
    company = db.relationship('Company', backref='late_fee_policies')
    client = db.relationship('Client', backref='late_fee_policies')
    created_by = db.relationship('User', backref='created_late_fee_policies')
    area_type = db.relationship('AreaType', backref='late_fee_policies')

    def __repr__(self):
        return f"<LateFeePolicy {self.applies_to} for Client {self.client_id}>"

