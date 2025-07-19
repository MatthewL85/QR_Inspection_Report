from app.extensions import db 
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class BankTransaction(db.Model):
    __tablename__ = 'bank_transactions'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Related Bank Account
    bank_account_id = db.Column(db.Integer, db.ForeignKey('bank_accounts.id'), nullable=False)
    bank_account = db.relationship('BankAccount', backref='transactions')

    # 📅 Transaction Core Fields
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(255), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'Credit' or 'Debit'
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    balance_after = db.Column(db.Numeric(14, 2), nullable=True)

    # 🔁 Optional Source Linking
    invoice_id = db.Column(
        db.Integer,
        db.ForeignKey('invoices.id', use_alter=True, name='fk_transaction_invoice', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    service_charge_payment_id = db.Column(
        db.Integer,
        db.ForeignKey('service_charge_payments.id', use_alter=True, name='fk_transaction_scp', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    levy_payment_id = db.Column(
        db.Integer,
        db.ForeignKey('levy_payments.id', use_alter=True, name='fk_transaction_levy', deferrable=True, initially='DEFERRED'),
        nullable=True
    )

    invoice = db.relationship('Invoice', backref='bank_transactions')
    service_charge_payment = db.relationship('ServiceChargePayment', backref='bank_transactions')
    levy_payment = db.relationship('LevyPayment', backref='bank_transactions')

    # 🔄 Reconciliation
    is_reconciled = db.Column(db.Boolean, default=False)

    reconciled_by_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', use_alter=True, name='fk_transaction_reconciled_by', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    reconciled_by = db.relationship('User', foreign_keys=[reconciled_by_id])
    reconciled_at = db.Column(db.DateTime, nullable=True)

    reconciliation_engine_id = db.Column(
        db.Integer,
        db.ForeignKey('reconciliation_engine.id', use_alter=True, name='fk_transaction_rec_engine', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    reconciliation_engine = db.relationship('ReconciliationEngine', backref='transactions')

    # ⚠️ Flags & Notes
    is_flagged = db.Column(db.Boolean, default=False)
    flagged_reason = db.Column(db.String(255), nullable=True)

    # 🤖 AI / GAR Enhancements
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    ai_confidence_score = db.Column(db.Float, nullable=True)
    flagged_by_gar = db.Column(db.Boolean, default=False)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    gar_notes = db.Column(db.Text, nullable=True)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 🌐 Integration Metadata
    external_ref = db.Column(db.String(150), nullable=True)
    integration_status = db.Column(db.String(50), nullable=True)

    # 🧑 Audit Info
    created_by_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', use_alter=True, name='fk_transaction_created_by', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<BankTransaction {self.transaction_type} {self.amount} | {self.description}>"
