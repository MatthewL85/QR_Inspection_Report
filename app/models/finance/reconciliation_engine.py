from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB

class ReconciliationEngine(db.Model):
    __tablename__ = 'reconciliation_engine'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Source Context
    bank_account_id = db.Column(db.Integer, db.ForeignKey('bank_accounts.id'), nullable=False)
    reconciliation_batch_id = db.Column(db.Integer, db.ForeignKey('reconciliation_batches.id'), nullable=True)
    initiated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)

    # 📥 Input Metadata
    imported_statement_file = db.Column(db.String(255), nullable=True)     # Uploaded file ref (CSV, PDF, etc.)
    imported_by_system = db.Column(db.String(100), nullable=True)          # System source or API
    system_snapshot_reference = db.Column(db.String(100), nullable=True)   # Timestamp/hash for snapshot comparison

    # ⚙️ Strategy & Matching Rules
    matching_method = db.Column(db.String(100), nullable=False, default='Multi-Pass AI')  # Exact, Fuzzy, Tolerance, AI, Manual
    match_tolerance_days = db.Column(db.Integer, default=3)
    amount_tolerance_cents = db.Column(db.Integer, default=100)
    include_pending_transactions = db.Column(db.Boolean, default=False)
    auto_confirm_high_confidence = db.Column(db.Boolean, default=True)

    # 🤖 AI + GAR Evaluation
    ai_confidence_threshold = db.Column(db.Float, default=0.85)
    ai_flagged_items = db.Column(JSONB, default={})             # {"unmatched": [...], "duplicates": [...], ...}
    ai_summary = db.Column(db.Text, nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    parsed_data = db.Column(db.JSON, nullable=True)
    gar_rules_applied = db.Column(JSONB, default={})            # Governance logic applied
    gar_risk_assessment = db.Column(db.Text, nullable=True)
    gar_score = db.Column(db.String(20), nullable=True)         # A+, B, Warning
    requires_human_review = db.Column(db.Boolean, default=True)
    approved_by_gar = db.Column(db.Boolean, default=False)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 📈 Matching Outcome
    total_entries_matched = db.Column(db.Integer, default=0)
    total_unmatched_entries = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float, default=0.0)             # 0.0 – 1.0
    final_status = db.Column(db.String(50), default='Draft')    # Draft, In Review, Completed, Failed
    reconciliation_status = db.Column(db.String(50), default="Unreconciled")

    # 📎 Output + Logs
    export_reference = db.Column(db.String(255), nullable=True)
    audit_log_reference = db.Column(db.String(255), nullable=True)
    reconciled_at = db.Column(db.DateTime, nullable=True)
    reconciled_by_ai_version = db.Column(db.String(50), nullable=True)
    reconciliation_notes = db.Column(db.Text, nullable=True)

    # 🔒 Security + Audit Trail
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔁 Relationships
    bank_account = db.relationship('BankAccount', backref='reconciliation_engines')
    reconciliation_batch = db.relationship('ReconciliationBatch', backref='reconciliation_engines')
    initiated_by = db.relationship('User', foreign_keys=[initiated_by_id])
    client = db.relationship('Client', backref='reconciliation_engines')
    unit = db.relationship('Unit', backref='reconciliation_engines')

    def __repr__(self):
        return f"<ReconciliationEngine Account={self.bank_account_id} | Matches={self.total_entries_matched} | Status={self.final_status}>"

