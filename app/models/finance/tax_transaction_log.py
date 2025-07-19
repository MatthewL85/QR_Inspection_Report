from app.extensions import db
from datetime import datetime

class TaxTransactionLog(db.Model):
    __tablename__ = 'tax_transaction_logs'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Source Links
    tax_rate_id = db.Column(db.Integer, db.ForeignKey('tax_rates.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    service_charge_id = db.Column(db.Integer, db.ForeignKey('service_charges.id'), nullable=True)
    levy_id = db.Column(db.Integer, db.ForeignKey('levies.id'), nullable=True)

    # 💰 Tax Breakdown
    tax_amount = db.Column(db.Numeric(10, 2), nullable=False)
    base_amount = db.Column(db.Numeric(10, 2), nullable=False)
    calculated_on = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

    # 🧠 AI / GAR Scanning
    parsed_summary = db.Column(db.Text, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    flagged_by_gar = db.Column(db.Boolean, default=False)
    gar_notes = db.Column(db.Text, nullable=True)
    gar_score = db.Column(db.Float, nullable=True)
    ai_tags = db.Column(db.JSON, nullable=True)  # e.g., {"classification": "standard VAT", "confidence": 0.92}

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🔐 Audit Trail
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🔁 Relationships
    tax_rate = db.relationship('TaxRate', backref='transactions')
    invoice = db.relationship('Invoice', backref='tax_logs')
    service_charge = db.relationship('ServiceCharge', backref='tax_logs')
    levy = db.relationship('Levy', backref='tax_logs')

    def __repr__(self):
        return f"<TaxTransactionLog Tax={self.tax_amount} | Base={self.base_amount} | RateID={self.tax_rate_id}>"
