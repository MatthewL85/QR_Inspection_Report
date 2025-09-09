from app.extensions import db
from datetime import datetime

class TaxRate(db.Model):
    __tablename__ = 'tax_rates'

    id = db.Column(db.Integer, primary_key=True)

    # 📌 Core Details
    name = db.Column(db.String(100), nullable=False)              # e.g., "Standard VAT"
    rate = db.Column(db.Float, nullable=False)                    # e.g., 23.0 for 23%
    tax_type = db.Column(db.String(50), default="VAT")            # VAT, GST, Local, Withholding, etc.

    # 🌍 Jurisdictional Coverage
    country = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(100), nullable=True)

    # 🗓 Effective Period
    effective_from = db.Column(db.Date, nullable=False)
    effective_to = db.Column(db.Date, nullable=True)

    # 🧠 AI / GAR Integration
    ai_classification = db.Column(db.String(255), nullable=True)     # e.g. "Reduced Rate - Services"
    parsed_summary = db.Column(db.Text, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    flagged_by_ai = db.Column(db.Boolean, default=False)
    gar_notes = db.Column(db.Text, nullable=True)
    gar_score = db.Column(db.Float, nullable=True)
    gar_decision_reason = db.Column(db.Text, nullable=True)

    # 🔐 Audit Trail + Governance
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    created_by = db.relationship('User', foreign_keys=[created_by_id])
    updated_by = db.relationship('User', foreign_keys=[updated_by_id])

    # 🔁 Relationships
    tax_transaction_logs = db.relationship('TaxTransactionLog', back_populates='tax_rate', lazy=True)

    def __repr__(self):
        return f"<TaxRate {self.name} | {self.rate}% ({self.country})>"

