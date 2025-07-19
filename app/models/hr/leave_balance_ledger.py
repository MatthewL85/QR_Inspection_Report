from datetime import datetime
from app.extensions import db

class LeaveBalanceLedger(db.Model):
    __tablename__ = 'leave_balance_ledger'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Who this record belongs to
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)           # Annual, Sick, Maternity, etc.
    period = db.Column(db.String(20), nullable=True)                # e.g., "2025", "Q1-2025"

    # 📊 Balances
    opening_balance = db.Column(db.Float, nullable=False, default=0.0)
    leave_accrued = db.Column(db.Float, nullable=False, default=0.0)
    leave_taken = db.Column(db.Float, nullable=False, default=0.0)
    carry_forward = db.Column(db.Float, nullable=True, default=0.0)
    closing_balance = db.Column(db.Float, nullable=True)

    # 🛠 Source Tracking
    source = db.Column(db.String(100), nullable=True)               # Manual, Automated, Import
    notes = db.Column(db.Text, nullable=True)

    # 📅 Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔍 AI Parsing / GAR Evaluation (Optional)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    parsed_at = db.Column(db.DateTime, nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)

    gar_flags = db.Column(db.Text, nullable=True)                   # e.g., "negative carry forward"
    gar_risk_score = db.Column(db.Float, nullable=True)
    gar_recommendation = db.Column(db.Text, nullable=True)

    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)


    # 🔗 Relationships
    user = db.relationship('User', backref='leave_balance_ledger')

    def __repr__(self):
        return f"<LeaveBalanceLedger user_id={self.user_id} leave_type={self.leave_type} closing_balance={self.closing_balance}>"

    # ✅ Best practice: this should be a staticmethod or a separate service
    @staticmethod
    def recalculate_balance(user_id, leave_type, period):
        ledger = LeaveBalanceLedger.query.filter_by(
            user_id=user_id,
            leave_type=leave_type,
            period=period
        ).first()

        if ledger:
            ledger.closing_balance = (
                ledger.opening_balance +
                ledger.leave_accrued -
                ledger.leave_taken +
                (ledger.carry_forward or 0)
            )
            db.session.commit()
