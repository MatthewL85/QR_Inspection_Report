from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import validates

class Income(db.Model):
    __tablename__ = 'incomes'

    id = db.Column(db.Integer, primary_key=True)

    # 🔐 Core Relationships
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False, index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True, index=True)

    # 💰 Income Details
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    date_received = db.Column(db.Date, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)
    source = db.Column(db.String(100), nullable=True)  # e.g., service charge, levy, grant, refund
    gl_code = db.Column(db.String(20), nullable=True)

    # 🧠 AI & GAR Enhancements
    ai_tag = db.Column(db.String(100), nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)
    gar_risk_flag = db.Column(db.Boolean, default=False)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    gar_notes = db.Column(db.Text, nullable=True)
    flagged_by_gar = db.Column(db.Boolean, default=False)
    context_tags = db.Column(db.ARRAY(db.String(50)), nullable=True)
    role_visibility = db.Column(db.ARRAY(db.String(50)), nullable=True)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🔌 3rd-Party Sync Fields
    external_reference = db.Column(db.String(100), nullable=True)
    external_system = db.Column(db.String(100), nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')  # Synced, Failed, Manual
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 📌 Context & Audit Trail
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

    # 🔁 Relationships
    company = db.relationship('Company', backref='incomes')
    client = db.relationship('Client', backref='incomes')
    unit = db.relationship('Unit', backref='incomes')
    created_by = db.relationship('User', backref='created_incomes', foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<Income {self.amount} received on {self.date_received}>"


