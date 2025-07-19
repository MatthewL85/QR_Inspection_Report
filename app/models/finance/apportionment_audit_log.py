from datetime import datetime
from app.extensions import db

class ApportionmentAuditLog(db.Model):
    __tablename__ = 'apportionment_audit_logs'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)

    # 📊 Allocation Details
    method = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    basis_value = db.Column(db.Numeric(12, 4), nullable=True)
    unit_size = db.Column(db.Numeric(12, 4), nullable=True)

    # 🤖 AI Reasoning / GAR
    ai_reasoning = db.Column(db.Text, nullable=True)
    gar_flagged = db.Column(db.Boolean, default=False)
    gar_notes = db.Column(db.Text, nullable=True)

    # 🕓 Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
