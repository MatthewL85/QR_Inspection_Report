from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

class Account(db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Key Relationships
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)  # Optional unit-level ledger
    finance_batch_id = db.Column(db.Integer, db.ForeignKey('finance_batches.id'), nullable=True)

    client = db.relationship("Client", backref="accounts")
    unit = db.relationship("Unit", backref="accounts")
    finance_batch = db.relationship('FinanceBatch', back_populates='linked_accounts')

    # 📘 Account Details
    account_name = db.Column(db.String(150), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)  # asset, liability, income, expense, equity
    balance = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    currency = db.Column(db.String(10), nullable=False, default='EUR')  # ISO code

    # 📌 Status & Classification
    is_active = db.Column(db.Boolean, default=True)
    access_level = db.Column(db.String(50), default='admin')  # admin, readonly, finance_controller
    tags = db.Column(ARRAY(db.String), nullable=True)

    # 📄 Metadata
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    last_modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    created_by = db.relationship("User", foreign_keys=[created_by_id])
    last_modified_by = db.relationship("User", foreign_keys=[last_modified_by_id])

    # 🧠 AI / GAR Fields
    parsed_text = db.Column(db.Text, nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)  # Optional scoring, compliance, or health check output
    is_flagged = db.Column(db.Boolean, default=False)  # For GAR/AI anomalies
    gar_context_reference = db.Column(db.String(255), nullable=True)
    gar_recommendation = db.Column(db.String(255), nullable=True)
    gar_risk_rating = db.Column(db.String(50), nullable=True)  # Optional: Low, Medium, High, Escalate
    flagged_reason = db.Column(db.Text, nullable=True)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    def __repr__(self):
        return f"<Account {self.account_name} ({self.account_type}) - Balance: {self.balance}>"

