# app/models/salary.py

from datetime import datetime
from app.extensions import db

class Salary(db.Model):
    __tablename__ = 'salaries'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    linked_contract_id = db.Column(db.Integer, nullable=True)  # Optionally link to EmploymentContract

    user = db.relationship("User", foreign_keys=[user_id], backref="salary_records")
    creator = db.relationship("User", foreign_keys=[created_by], backref="created_salaries")

    # 💸 Salary Core Info
    payment_type = db.Column(db.String(50))                    # Monthly, Hourly, Flat Fee
    amount = db.Column(db.Numeric(10, 2))
    currency = db.Column(db.String(5))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date, nullable=True)
    employment_type = db.Column(db.String(50), nullable=True)  # Full-Time, Part-Time, Contractor
    salary_band = db.Column(db.String(50), nullable=True)      # A, B, C, D, etc.
    notes = db.Column(db.Text)

    # 🔐 Visibility & Role Access
    visibility_scope = db.Column(db.String(100), default='Admin,HR')
    is_private = db.Column(db.Boolean, default=True)
    shared_with_director = db.Column(db.Boolean, default=False)
    consent_verified = db.Column(db.Boolean, default=False)

    # 🔌 External API Fields
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')
    is_external = db.Column(db.Boolean, default=False)

    # 🤖 AI / GAR Integration
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_confidence_score = db.Column(db.Float, nullable=True)
    ai_profile_locked = db.Column(db.Boolean, default=False)
    flagged_sections = db.Column(db.JSON, nullable=True)        # {"amount": "mismatch", "currency": "unclear"}

    # 🧠 GAR Compliance Fields
    gar_flags = db.Column(db.Text, nullable=True)
    gar_compliance_score = db.Column(db.Float, nullable=True)
    gar_comments = db.Column(db.Text, nullable=True)
    requires_hr_review = db.Column(db.Boolean, default=False)
    is_approved_by_hr = db.Column(db.Boolean, default=False)
    approved_at = db.Column(db.DateTime, nullable=True)
    review_notes = db.Column(db.Text, nullable=True)

    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Salary user_id={self.user_id} amount={self.amount} {self.currency}>"

