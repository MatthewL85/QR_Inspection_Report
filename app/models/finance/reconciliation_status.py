# app/models/finance/reconciliation_status.py

from app.extensions import db
from datetime import datetime

class ReconciliationStatus(db.Model):
    __tablename__ = 'reconciliation_statuses'

    id = db.Column(db.Integer, primary_key=True)

    # 📊 Status Label & Description
    status = db.Column(db.String(50), unique=True, nullable=False)  # e.g., Matched, Partially Matched, Flagged, Rejected
    description = db.Column(db.Text, nullable=True)                 # Human-readable explanation
    category = db.Column(db.String(50), nullable=True)              # Optional groupings: Success, Warning, Error

    # 🧠 AI & GAR Fields
    is_flagged_by_gar = db.Column(db.Boolean, default=False)
    gar_risk_score = db.Column(db.Float, nullable=True)
    gar_reason = db.Column(db.String(255), nullable=True)
    recommended_action = db.Column(db.String(255), nullable=True)   # e.g., "Hold for review", "Auto-clear", etc.

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🕵️ Audit Metadata
    is_system_generated = db.Column(db.Boolean, default=False)      # True if auto-assigned by the engine
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 🔁 Relationships
    created_by = db.relationship('User', backref='created_reconciliation_statuses', foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<ReconciliationStatus {self.status}>"
