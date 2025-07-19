# app/models/finance/cross_border_tax_compliance.py

from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB

class CrossBorderTaxCompliance(db.Model):
    __tablename__ = 'cross_border_tax_compliance'

    id = db.Column(db.Integer, primary_key=True)

    # 🌍 Core Tax Info
    transaction_type = db.Column(db.String(100), nullable=False)  # e.g., Service Export, Digital Services, eCommerce
    origin_country = db.Column(db.String(100), nullable=False)
    destination_country = db.Column(db.String(100), nullable=False)
    tax_rate_applied = db.Column(db.Numeric(5, 2), nullable=True)
    tax_code = db.Column(db.String(50), nullable=True)  # OSS, MOSS, VAT, GST
    is_reverse_charge = db.Column(db.Boolean, default=False)
    is_tax_exempt = db.Column(db.Boolean, default=False)
    exemption_reason = db.Column(db.String(255), nullable=True)
    compliance_notes = db.Column(db.Text)

    # 🔗 Relationships
    related_invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    related_transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)

    invoice = db.relationship('Invoice', backref='cross_border_tax_compliance')
    transaction = db.relationship('Transaction', backref='cross_border_tax_entries')
    client = db.relationship('Client', backref='cross_border_tax_compliance')

    # 🤖 AI / GAR Fields
    flagged_by_gar = db.Column(db.Boolean, default=False)
    gar_risk_level = db.Column(db.String(50), nullable=True)  # Low, Medium, High
    gar_notes = db.Column(db.Text, nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🔌 3rd-Party Integration Support
    external_tax_service_id = db.Column(db.String(100), nullable=True)  # e.g., Avalara, TaxJar ID
    integration_status = db.Column(db.String(50), nullable=True)  # Synced, Pending, Failed
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 🔐 Audit Info
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    modified_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    modified_by = db.relationship('User', foreign_keys=[modified_by_id])

    def __repr__(self):
        return f"<CrossBorderTaxCompliance {self.transaction_type} {self.origin_country}->{self.destination_country} rate={self.tax_rate_applied}%>"
