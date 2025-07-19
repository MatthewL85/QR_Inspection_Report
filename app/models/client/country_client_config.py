from datetime import datetime
from sqlalchemy.orm import validates
from app.extensions import db
from app.utils.json_helpers import ensure_json_string  # ✅ Required for validation

class CountryClientConfig(db.Model):
    __tablename__ = 'country_client_config'

    id = db.Column(db.Integer, primary_key=True)

    # 🌍 Core Jurisdictional Metadata
    country = db.Column(db.String(100), nullable=False)
    client_type = db.Column(db.String(100), nullable=False)        # HOA, MCST, OMC, etc.
    legal_basis = db.Column(db.String(500), nullable=True)         # Governing legislation citation
    governing_body = db.Column(db.String(150), nullable=True)
    currency = db.Column(db.String(10), nullable=True)
    language = db.Column(db.String(50), default='English')

    # 🧩 Configurable Lists (stored as JSON-encoded strings)
    ownership_types = db.Column(db.Text)                           # JSON: ["Freehold", "Leasehold"]
    timezones = db.Column(db.Text)                                 # JSON: ["UTC", "GMT+1"]
    regions = db.Column(db.Text)                                   # JSON: ["Dublin", "Munster"]

    # 🛡️ Legal/Regulatory Structure
    is_commercial = db.Column(db.Boolean, default=False)           # Flag for commercial setups
    deed_required = db.Column(db.Boolean, default=True)
    min_directors = db.Column(db.Integer)
    max_directors = db.Column(db.Integer)

    # 🔐 Resident Logic & Privacy Framework
    resident_equivalence_logic = db.Column(db.String(100), default='owner=member, tenant=resident')
    data_protection_compliance = db.Column(db.Boolean, default=True)
    requires_gdpr_consent = db.Column(db.Boolean, default=True)
    default_visibility_scope = db.Column(db.String(100), default="Admin,Director,PropertyManager")  # API scope

    # 📅 Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🤖 AI Parsing Metadata (Phase 1)
    document_filename = db.Column(db.String(255))
    ai_parsed_legal_summary = db.Column(db.Text)
    ai_key_clauses = db.Column(db.JSON, nullable=True)             # Parsed obligations and clauses
    ai_risks_or_exceptions = db.Column(db.Text)
    ai_ownership_recommendations = db.Column(db.Text)
    ai_timezone_map = db.Column(db.Text)                           # JSON: {"Dublin": "GMT", ...}
    ai_region_map = db.Column(db.Text)                             # JSON: {"Munster": "South"}
    ai_source_type = db.Column(db.String(50))                      # PDF, API, Manual
    ai_confidence_score = db.Column(db.Float, nullable=True)
    ai_parsed_at = db.Column(db.DateTime)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)

    # 🧠 GAR Governance & Recommendation Fields (Phase 2)
    gar_legal_alignment_rating = db.Column(db.String(20))          # Aligned, Partial, Misaligned
    gar_recommended_tag = db.Column(db.String(100))                # Best practice, Legacy, High Risk
    gar_summary_recommendation = db.Column(db.Text)
    gar_flagged_policy_gaps = db.Column(db.Text)

    # 💬 GAR Chat & AI Feedback
    gar_chat_ready = db.Column(db.Boolean, default=False)          # Enable chat interaction with GAR
    gar_feedback = db.Column(db.Text, nullable=True)
    gar_last_message_at = db.Column(db.DateTime, nullable=True)
    gar_resolution_status = db.Column(db.String(50), default='Open')  # Open, Reviewed, Escalated

    # 📜 Verification Metadata
    last_verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    verifier = db.relationship("User", foreign_keys=[last_verified_by])

    # ✅ Validation for JSON-encoded strings
    @validates('ownership_types', 'timezones', 'regions', 'ai_timezone_map', 'ai_region_map')
    def validate_json_strings(self, key, value):
        return ensure_json_string(value)

    def __repr__(self):
        return f"<CountryClientConfig {self.country} - {self.client_type}>"
