from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import validates

class LateFeeTransactionLog(db.Model):
    __tablename__ = 'late_fee_transaction_logs'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Associations
    policy_id = db.Column(db.Integer, db.ForeignKey('late_fee_interest_policies.id'), nullable=False, index=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    arrears_id = db.Column(db.Integer, db.ForeignKey('arrears.id'), nullable=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False, index=True)

    # 💸 Fee Details
    fee_amount = db.Column(db.Numeric(10, 2), nullable=True)
    interest_amount = db.Column(db.Numeric(10, 2), nullable=True)
    total_penalty = db.Column(db.Numeric(10, 2), nullable=False)
    compounded = db.Column(db.Boolean, default=False)
    waived = db.Column(db.Boolean, default=False)
    waiver_reason = db.Column(db.Text, nullable=True)
    policy_name_snapshot = db.Column(db.String(100), nullable=True)

    # 🤖 AI / GAR Integration
    ai_flagged = db.Column(db.Boolean, default=False)
    parsed_summary = db.Column(db.Text, nullable=True)
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)
    gar_compliance_score = db.Column(db.Float, nullable=True)
    gar_risk_flag = db.Column(db.String(50), nullable=True)  # Low, Medium, High
    gar_note = db.Column(db.Text, nullable=True)
    validated_by_gar = db.Column(db.Boolean, default=False)
    context_tags = db.Column(db.ARRAY(db.String(50)), nullable=True)
    role_visibility = db.Column(db.ARRAY(db.String(50)), nullable=True)

    # 🔌 3rd-Party Sync Fields
    external_reference = db.Column(db.String(100), nullable=True)
    external_system = db.Column(db.String(100), nullable=True)     # e.g., 'Yardi', 'MRI'
    sync_status = db.Column(db.String(50), default='Pending')      # Synced, Failed, Manual
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # ⏱ Metadata + Audit Trail
    applied_on = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 🔁 Relationships
    policy = db.relationship('LateFeeAndInterestPolicy', backref='fee_logs')
    invoice = db.relationship('Invoice', back_populates='late_fee_logs')
    arrears = db.relationship("Arrears", back_populates="late_fee_logs")
    unit = db.relationship('Unit', backref='late_fee_logs')
    client = db.relationship('Client', backref='late_fee_logs')
    created_by = db.relationship('User', backref='created_late_fee_logs')

    def __repr__(self):
        return f"<LateFeeLog unit_id={self.unit_id} total_penalty={self.total_penalty}>"
