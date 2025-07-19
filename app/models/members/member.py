# app/models/members/member.py

from app.extensions import db
from datetime import datetime

# 🔗 Many-to-Many Member <-> Unit association
member_units = db.Table(
    'member_units',
    db.Column('member_id', db.Integer, db.ForeignKey('members.id'), primary_key=True),
    db.Column('unit_id', db.Integer, db.ForeignKey('units.id'), primary_key=True),
    db.Column('ownership_percentage', db.Float, nullable=True),
)

class Member(db.Model):
    __tablename__ = 'members'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Nullable if company owner
    user = db.relationship('User', backref='memberships', lazy=True)

    units = db.relationship('Unit', secondary='member_units', back_populates='members')

    # 🧾 Governance & Consent
    contact_consent = db.Column(db.Boolean, default=True)
    data_sharing_opt_in = db.Column(db.Boolean, default=False)
    share_profile_with_directors = db.Column(db.Boolean, default=False)

    # 🔗 External Systems / API Ready
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    is_external = db.Column(db.Boolean, default=False)

    # 🕒 Timestamps
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🤖 AI Parsing & GAR Governance
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_profile_locked = db.Column(db.Boolean, default=False)  # ✅ Prevent further parsing unless unlocked

    # ⚖️ GAR Evaluation
    gar_risk_flags = db.Column(db.Text, nullable=True)
    gar_alignment_score = db.Column(db.Float, nullable=True)
    gar_trust_score = db.Column(db.Float, nullable=True)
    gar_recommendation = db.Column(db.String(255), nullable=True)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)


    # 🗳️ AGM Approvals (optional governance model)
    approvals = db.relationship('MemberApproval', backref='member', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Member id={self.id} user_id={self.user_id}>"


