from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class CreditNote(db.Model):
    __tablename__ = 'credit_notes'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Associations
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False, index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True, index=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    issued_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    applied_to_payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=True)

    # 🧾 Credit Note Details
    credit_note_number = db.Column(db.String(100), unique=True, nullable=False, index=True)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    credit_amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    reason = db.Column(db.String(255), nullable=False)

    # 📦 Application Tracking
    applied = db.Column(db.Boolean, default=False)
    applied_date = db.Column(db.DateTime, nullable=True)

    # 🤖 AI + GAR Enhancements
    ai_generated_summary = db.Column(db.Text, nullable=True)
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)
    gar_reviewed = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    flagged_by_gar = db.Column(db.Boolean, default=False)
    smart_tags = db.Column(JSONB, nullable=True)
    context_tags = db.Column(db.ARRAY(db.String(50)), nullable=True)
    role_visibility = db.Column(db.ARRAY(db.String(50)), nullable=True)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🔌 3rd-Party Integration
    external_reference = db.Column(db.String(100), nullable=True)
    external_system = db.Column(db.String(100), nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')  # Synced, Failed, Manual
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 📅 Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔁 Relationships
    client = db.relationship('Client', backref='credit_notes')
    unit = db.relationship('Unit', backref='credit_notes')
    invoice = db.relationship('Invoice', backref='credit_notes')
    payment = db.relationship('Payment', backref='credit_notes_applied')
    issued_by = db.relationship('User', backref='issued_credit_notes')

    def __repr__(self):
        return f"<CreditNote #{self.credit_note_number} amount={self.credit_amount}>"

