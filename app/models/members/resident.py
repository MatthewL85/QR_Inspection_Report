# models/members/resident.py

from datetime import datetime
from app.extensions import db

class Resident(db.Model):
    __tablename__ = 'residents'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'))

    user = db.relationship('User', backref='resident_profile', uselist=False)
    unit = db.relationship('Unit', backref='residents')

    # 🧾 Residency Approval
    approved_by_member = db.Column(db.Boolean, default=False)
    approved_at = db.Column(db.DateTime, nullable=True)
    is_current_resident = db.Column(db.Boolean, default=True)
    move_in_date = db.Column(db.Date, nullable=True)
    move_out_date = db.Column(db.Date, nullable=True)

    # 🔐 GDPR / Privacy
    consent_to_contact = db.Column(db.Boolean, default=False)
    data_sharing_opt_in = db.Column(db.Boolean, default=False)
    share_info_with_directors = db.Column(db.Boolean, default=False)

    # 🔌 External Integration
    external_reference = db.Column(db.String(100), nullable=True)
    is_external = db.Column(db.Boolean, default=False)
    source_system = db.Column(db.String(100), nullable=True)

    # 🤖 AI & GAR Evaluation
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    gar_profile_risk_score = db.Column(db.Float, nullable=True)
    gar_flags = db.Column(db.Text, nullable=True)
    gar_recommendation = db.Column(db.String(255), nullable=True)
    is_gar_reviewed = db.Column(db.Boolean, default=False)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_profile_locked = db.Column(db.Boolean, default=False)  # Prevent re-parsing after review

    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return (
            f"<Resident user_id={self.user_id} unit_id={self.unit_id} "
            f"current={self.is_current_resident}>"
        )

