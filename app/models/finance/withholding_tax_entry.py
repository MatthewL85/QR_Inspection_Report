from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class WithholdingTaxEntry(db.Model):
    __tablename__ = 'withholding_tax_entries'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Associations
    contractor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)

    # 💸 Tax Data
    amount_withheld = db.Column(db.Numeric(10, 2), nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    tax_code = db.Column(db.String(50), nullable=True)         # RCT, CIS, 1099, etc.
    jurisdiction = db.Column(db.String(100), nullable=True)
    remitted_to_tax_authority = db.Column(db.Boolean, default=False)
    remittance_date = db.Column(db.DateTime, nullable=True)

    # 📎 Evidence & Compliance
    remittance_reference = db.Column(db.String(100), nullable=True)
    supporting_documents_url = db.Column(db.String(255), nullable=True)  # Encrypted or presigned S3 link

    # 🤖 AI / GAR Enhancements
    gar_context_reference = db.Column(db.String(100), nullable=True)
    flagged_by_gar = db.Column(db.Boolean, default=False)
    gar_notes = db.Column(db.Text, nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)

    # 🔐 GDPR + Security Logging
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    # 🕵️ Full Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', foreign_keys=[created_by_id])
    modified_by = db.relationship('User', foreign_keys=[modified_by_id])
    contractor = db.relationship('User', foreign_keys=[contractor_id])

    # 🔁 Relationships
    invoice = db.relationship('Invoice', backref='withholding_entries')
    client = db.relationship('Client', backref='withholding_tax_entries')
    unit = db.relationship('Unit', backref='withholding_tax_entries')

    def __repr__(self):
        return f"<WithholdingTaxEntry contractor={self.contractor_id} invoice={self.invoice_id} amount={self.amount_withheld}>"

