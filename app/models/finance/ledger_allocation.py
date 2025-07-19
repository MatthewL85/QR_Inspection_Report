from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class LedgerAllocation(db.Model):
    __tablename__ = 'ledger_allocations'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    finance_batch_id = db.Column(db.Integer, db.ForeignKey('finance_batches.id'), nullable=True)
    ledger_entry_id = db.Column(db.Integer, db.ForeignKey('ledger_entries.id'), nullable=False)

    # 🎯 Allocation Targets
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=True)
    levy_id = db.Column(db.Integer, db.ForeignKey('levies.id'), nullable=True)
    service_charge_id = db.Column(db.Integer, db.ForeignKey('service_charges.id'), nullable=True)

    # 💰 Financial Details
    allocated_amount = db.Column(db.Numeric(14, 2), nullable=False)
    allocation_date = db.Column(db.DateTime, default=datetime.utcnow)
    allocation_type = db.Column(db.String(50), default='Manual')  # Manual, Auto, Adjustment

    # 🔐 Role-Based & Data Sensitivity
    status = db.Column(db.String(50), default='Posted')  # Draft, Posted, Voided
    is_active = db.Column(db.Boolean, default=True)
    access_scope = db.Column(db.String(50), default='Finance')  # Finance, PM, Admin
    is_sensitive = db.Column(db.Boolean, default=False)

    # 🧠 AI / GAR Enrichment
    ai_parsed_summary = db.Column(db.Text, nullable=True)
    ai_extracted_data = db.Column(JSONB, nullable=True)
    ai_tags = db.Column(JSONB, nullable=True)
    ai_score = db.Column(db.Numeric(5, 2), nullable=True)
    ai_notes = db.Column(db.Text, nullable=True)
    ai_confidence_score = db.Column(db.Numeric(5, 2), nullable=True)
    ai_model_used = db.Column(db.String(100), nullable=True)

    # 🤖 GAR Chat & Querying
    gar_query_context = db.Column(JSONB, nullable=True)
    gar_conversation_log = db.Column(JSONB, nullable=True)
    gar_message_context = db.Column(JSONB, nullable=True)

    # ⭐ GAR Feedback & Supervision Loop
    gar_feedback = db.Column(db.Text, nullable=True)
    gar_rating = db.Column(db.String(10), nullable=True)  # e.g., Excellent, Good, Fair, Poor
    gar_resolution_flag = db.Column(db.Boolean, default=False)  # Has the issue been resolved based on GAR output?

    # 🌐 3rd-Party Sync
    external_reference = db.Column(db.String(150), nullable=True)
    integration_status = db.Column(db.String(50), default='Pending')  # Synced, Pending, Error

    # 🧾 Source + Audit Metadata
    source_module = db.Column(db.String(100), nullable=True)  # e.g., 'Finance Logix', 'GAR Bot'
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
