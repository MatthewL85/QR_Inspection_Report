from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class Debtor(db.Model):
    __tablename__ = 'debtors'

    id = db.Column(db.Integer, primary_key=True)

    # 🧍 Individual Info
    name = db.Column(db.String(255), nullable=False, index=True)
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(50), nullable=True)

    # 🏢 Unit / Client Linkage
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False, index=True)

    # 💳 Financial Metadata
    account_number = db.Column(db.String(100), nullable=True, index=True)
    balance_due = db.Column(db.Float, default=0.0)
    credit_limit = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), default='active', index=True)  # active, suspended, closed

    # 🗓️ Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_payment_date = db.Column(db.DateTime, nullable=True)
    next_due_date = db.Column(db.Date, nullable=True)

    # 🔒 Audit Trail
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 🤖 AI / GAR Integration
    parsed_summary = db.Column(db.Text, nullable=True)
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)
    flagged_by_ai = db.Column(db.Boolean, default=False)
    reason_for_flag = db.Column(db.String(255), nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    context_tags = db.Column(db.ARRAY(db.String(50)), nullable=True)
    role_visibility = db.Column(db.ARRAY(db.String(50)), nullable=True)

    # 🔌 External Sync Info
    external_reference = db.Column(db.String(100), nullable=True)  # External accounting system ID
    external_system = db.Column(db.String(100), nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')  # Synced, Failed, Manual
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 🔁 Relationships
    unit = db.relationship('Unit', backref='debtors')
    client = db.relationship('Client', backref='debtors')
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<Debtor {self.name} | Balance: €{self.balance_due}>"

