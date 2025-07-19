from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class GeneralLedgerEntry(db.Model):
    __tablename__ = 'general_ledger_entries'

    id = db.Column(db.Integer, primary_key=True)
    entry_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 📄 Description & Classification
    description = db.Column(db.String(255), nullable=False)
    reference = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # 📚 Account Mapping
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False, index=True)
    account = db.relationship('Account', backref='ledger_entries')

    # 💰 Amounts
    debit_amount = db.Column(db.Numeric(12, 2), default=0.00, nullable=False)
    credit_amount = db.Column(db.Numeric(12, 2), default=0.00, nullable=False)

    # 🔗 Source Transaction (optional)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=True)
    transaction = db.relationship('Transaction', backref='ledger_entries')

    # 🔐 Security & Audit Trail
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    # 🤖 AI / GAR Enhancements
    parsed_summary = db.Column(db.Text, nullable=True)
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)
    ai_generated_tags = db.Column(db.ARRAY(db.String), nullable=True)
    ai_notes = db.Column(db.Text, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    flagged_by_ai = db.Column(db.Boolean, default=False)
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

    # ⚙️ Control Flags
    is_adjustment = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)  # Locked entries require Super Admin override

    def __repr__(self):
        return f"<GL Entry {self.id} | {self.entry_date.date()} | Account {self.account_id}>"

