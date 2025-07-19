from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class BankAccount(db.Model):
    __tablename__ = 'bank_accounts'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Ownership
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    client = db.relationship('Client', backref='bank_accounts')

    # 🏦 Core Details
    account_type = db.Column(db.String(50), nullable=False)  # Operating, Sinking Fund, Reserve Fund
    account_name = db.Column(db.String(100), nullable=False)
    account_number_masked = db.Column(db.String(50), nullable=True)  # Masked: last 4 digits only
    bank_name = db.Column(db.String(100), nullable=True)
    iban = db.Column(db.String(50), nullable=True)
    bic = db.Column(db.String(20), nullable=True)
    currency = db.Column(db.String(10), default='EUR')

    # 💰 Balances & Syncing
    opening_balance = db.Column(db.Numeric(14, 2), default=0.00)
    current_balance = db.Column(db.Numeric(14, 2), default=0.00)
    last_synced_at = db.Column(db.DateTime, nullable=True)
    is_live_linked = db.Column(db.Boolean, default=False)
    banking_provider = db.Column(db.String(100), nullable=True)  # e.g., Plaid, TrueLayer, Yodlee
    sync_status = db.Column(db.String(50), nullable=True)        # Synced, Error, Pending

    # 🔐 Security & Access Control
    encryption_reference = db.Column(db.String(255), nullable=True)  # Encrypted token ref for external API
    access_revoked = db.Column(db.Boolean, default=False)
    audit_consent_reference = db.Column(db.String(255), nullable=True)  # PDF ref or document ID

    # 🤖 AI / GAR Enhancements
    gar_context_reference = db.Column(db.String(100), nullable=True)
    flagged_by_gar = db.Column(db.Boolean, default=False)
    gar_notes = db.Column(db.Text, nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)  # {"linked_tx_count": 123, "outlier_tx": [...]}    
    ai_risk_score = db.Column(db.Float, nullable=True)  # Probability of fraudulent or out-of-bounds activity
    ai_recommendation = db.Column(db.Text, nullable=True)
    is_gar_verified = db.Column(db.Boolean, default=False)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 👤 Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<BankAccount {self.account_name} | Type: {self.account_type} | Balance: {self.current_balance}>"

