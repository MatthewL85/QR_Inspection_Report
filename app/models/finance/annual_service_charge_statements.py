# app/models/finance/annual_service_charge_statements.py

from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class AnnualServiceChargeStatement(db.Model):
    __tablename__ = 'annual_service_charge_statements'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    client = db.relationship('Client', backref='annual_service_charge_statements')
    unit = db.relationship('Unit', backref='annual_service_charge_statements')

    # 📅 Period Covered
    year = db.Column(db.Integer, nullable=False)
    period_label = db.Column(db.String(100), default='Annual')  # Optional: FY2024/25
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    # 💰 Financial Summary
    total_charged = db.Column(db.Numeric(12, 2), nullable=False)
    total_paid = db.Column(db.Numeric(12, 2), default=0)
    total_outstanding = db.Column(db.Numeric(12, 2), default=0)
    late_fees_applied = db.Column(db.Numeric(12, 2), default=0)
    interest_applied = db.Column(db.Numeric(12, 2), default=0)

    # 📄 Documentation
    statement_url = db.Column(db.String(255), nullable=True)     # Path to PDF summary
    supporting_documents = db.Column(JSONB, nullable=True)       # List of document references or metadata

    # 🤖 AI / GAR Fields
    parsed_summary = db.Column(db.Text, nullable=True)           # Textual summary of charges/notes
    extracted_data = db.Column(JSONB, nullable=True)             # Breakdown of charges by category
    gar_score = db.Column(db.Float, nullable=True)               # GAR confidence or risk score (0–1)
    gar_flagged = db.Column(db.Boolean, default=False)
    gar_flag_reason = db.Column(db.String(255), nullable=True)
    ai_notes = db.Column(db.Text, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    is_gar_verified = db.Column(db.Boolean, default=False)

    # ✅ Validation & Status
    is_finalised = db.Column(db.Boolean, default=False)
    validated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    validated_by = db.relationship('User', foreign_keys=[validated_by_id])
    validated_at = db.Column(db.DateTime)

    # 🌐 External Integration Support
    integration_status = db.Column(db.String(50), nullable=True)  # Synced, Failed, Pending
    external_reference = db.Column(db.String(150), nullable=True) # e.g., external accounting ID

    # 🕓 Audit & Ownership
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AnnualServiceChargeStatement unit={self.unit_id} year={self.year}>"
