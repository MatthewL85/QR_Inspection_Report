# app/models/finance/budget_allocation_log.py

from datetime import datetime
from app.extensions import db

class BudgetAllocationLog(db.Model):
    __tablename__ = 'budget_allocation_logs'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    calculated_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    unit = db.relationship("Unit", backref="allocation_logs")
    client = db.relationship("Client", backref="budget_allocation_logs")
    calculated_by = db.relationship("User", foreign_keys=[calculated_by_user_id])
    approved_by = db.relationship("User", foreign_keys=[approved_by_user_id])

    # 💰 Budget Info
    total_budget_amount = db.Column(db.Numeric(12, 2), nullable=False)
    allocated_amount = db.Column(db.Numeric(12, 2), nullable=False)
    allocation_method = db.Column(db.String(50), nullable=False)  # Equal, Percentage, UnitSize, AIWeighted
    apportionment_value = db.Column(db.Float, nullable=True)      # e.g., 12.5% or 55.0 sqm

    # 🧠 AI & GAR Enrichment
    ai_flagged = db.Column(db.Boolean, default=False)
    ai_confidence = db.Column(db.Float, nullable=True)
    gar_flag = db.Column(db.Boolean, default=False)
    gar_reason = db.Column(db.Text, nullable=True)
    gar_risk_score = db.Column(db.Float, nullable=True)           # 0.0 – 1.0
    parsed_summary = db.Column(db.Text, nullable=True)
    ai_comments = db.Column(db.Text, nullable=True)

    # 📅 Metadata
    allocation_period = db.Column(db.String(20), nullable=True)   # e.g., "2024-2025"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

    # ✅ AGM Approval Lifecycle
    is_draft = db.Column(db.Boolean, default=True)                # Becomes False once passed at AGM
    agm_date = db.Column(db.DateTime, nullable=True)
    agm_reference = db.Column(db.String(100), nullable=True)      # e.g., "AGM 2025 Resolution 4"
    approved_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<BudgetAllocationLog unit_id={self.unit_id} amount={self.allocated_amount} method={self.allocation_method} draft={self.is_draft}>"
