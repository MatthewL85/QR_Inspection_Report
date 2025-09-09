# app/models/audit/contract_audit.py
from __future__ import annotations
from datetime import datetime
from app.extensions import db

class ContractAudit(db.Model):
    __tablename__ = "contract_audits"

    id = db.Column(db.Integer, primary_key=True)

    # The contract this audit row belongs to
    contract_id = db.Column(db.Integer, db.ForeignKey("client_contracts.id"), nullable=False, index=True)

    # Optional: who performed the action (if available)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    # action: "create_draft" | "inline_update" | "apply_update" | ...
    action = db.Column(db.String(64), nullable=False)

    # JSON string with details (changed fields, accepted sections, etc.)
    detail_json = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    contract = db.relationship("ClientContract", backref="audits")
