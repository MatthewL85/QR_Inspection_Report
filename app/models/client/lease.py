# app/models/lease.py

from datetime import datetime
from app.extensions import db

class Lease(db.Model):
    __tablename__ = 'leases'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Owner (optional for commercial)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    country_config_id = db.Column(db.Integer, db.ForeignKey('country_client_config.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # PM/admin who created

    # 📄 Lease Details
    lease_type = db.Column(db.String(50))                             # Residential, Commercial, Mixed
    lease_status = db.Column(db.String(50), default='Active')         # Active, Terminated, Expired, Suspended
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    renewal_terms = db.Column(db.Text)
    auto_renew_enabled = db.Column(db.Boolean, default=False)         # ✅ Optional for automation logic
    notice_period_days = db.Column(db.Integer)

    # 💰 Financial Terms
    rent_amount = db.Column(db.Numeric(10, 2), nullable=False)
    rent_currency = db.Column(db.String(10), default='EUR')
    billing_cycle = db.Column(db.String(50))                          # Monthly, Quarterly, Annually
    service_charge_contribution = db.Column(db.Numeric(10, 2))
    late_payment_penalty = db.Column(db.String(100))                 # e.g., "5% per month", "Flat €50"

    # 🏢 Commercial Lease Clauses
    permitted_use = db.Column(db.String(255))                         # e.g., "Retail", "Office"
    rent_review_frequency = db.Column(db.String(50))                  # Annually, Every 5 Years
    break_clause = db.Column(db.String(255))
    insurance_requirements = db.Column(db.Text)
    common_area_usage_terms = db.Column(db.Text)

    # 📎 Lease Files
    document_filename = db.Column(db.String(255))
    document_path = db.Column(db.String(255))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    # 🤖 AI Parsing Enhancements
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)               # Parsed fields like rent, notice, break clause
    parsing_status = db.Column(db.String(50), default='Pending')     # Pending, Completed, Failed
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50))                        # PDF, Scan, Upload, etc.
    is_ai_processed = db.Column(db.Boolean, default=False)

    # 🧠 GAR Risk & Governance Fields
    gar_compliance_score = db.Column(db.Float)                       # 0.0–1.0
    gar_flagged_issues = db.Column(db.Text)                          # e.g., "Break clause missing"
    gar_key_clauses = db.Column(db.JSON)                             # e.g., {"rent_review": "every 5 years", ...}
    gar_action_required = db.Column(db.String(255))                  # "Escalate", "Legal Review"
    is_gar_reviewed = db.Column(db.Boolean, default=False)

    # 💬 GAR Chat & Feedback Fields
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)
    gar_last_message_at = db.Column(db.DateTime, nullable=True)
    gar_resolution_status = db.Column(db.String(50), default='Open')  # Open, In Progress, Resolved, Escalated

    # 📅 Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔁 Relationships
    unit = db.relationship('Unit', backref='leases')
    tenant = db.relationship('User', foreign_keys=[tenant_id], backref='leases_as_tenant')
    member = db.relationship('User', foreign_keys=[member_id], backref='leases_as_member')
    client = db.relationship('Client', backref='leases')
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='leases_created')
    country_config = db.relationship('CountryClientConfig', backref='leases')

    def __repr__(self):
        return f"<Lease id={self.id} tenant={self.tenant_id} unit={self.unit_id} status={self.lease_status}>"

