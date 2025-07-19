from datetime import datetime
from app.extensions import db

class EmployeeExitProcess(db.Model):
    __tablename__ = 'employee_exit_processes'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    initiated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    termination_record_id = db.Column(db.Integer, db.ForeignKey('termination_records.id'), nullable=True)

    # 📋 Exit Process Metadata
    status = db.Column(db.String(50), default='Pending')  # Pending, In Progress, Completed, Cancelled
    checklist_status = db.Column(db.JSON, default={})     # {"access_revoked": True, "docs_returned": False}
    final_day = db.Column(db.Date, nullable=True)
    exit_type = db.Column(db.String(50), nullable=True)   # Voluntary, Redundancy, Dismissal
    reason_for_exit = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # 🧠 AI / GAR Processing (Phase 1 & 2 Ready)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)         # e.g., checklist mapping
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    parsed_at = db.Column(db.DateTime, nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)

    gar_risk_score = db.Column(db.Float, nullable=True)         # e.g., legal or compliance risk
    gar_flags = db.Column(db.Text, nullable=True)
    gar_recommendation = db.Column(db.Text, nullable=True)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 📅 Meta
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔁 Relationships
    user = db.relationship("User", foreign_keys=[user_id], backref="exit_processes")
    initiated_by = db.relationship("User", foreign_keys=[initiated_by_id], backref="exit_initiated")
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id], backref="exit_reviewed")
    termination_record = db.relationship("TerminationRecord", backref="exit_process", uselist=False)

    def __repr__(self):
        return f"<EmployeeExitProcess user_id={self.user_id} status='{self.status}'>"
