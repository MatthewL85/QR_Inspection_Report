from datetime import datetime
from app.extensions import db

class CapexResponse(db.Model):
    __tablename__ = 'capex_responses'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Linkage
    capex_request_id = db.Column(db.Integer, db.ForeignKey('capex_requests.id'), nullable=False)
    submitted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 📄 Quote Info
    contractor_name = db.Column(db.String(100), nullable=False)
    quote_amount = db.Column(db.Float, nullable=False)
    file = db.Column(db.String(200))                             # Uploaded file path
    notes = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🤖 AI Parsing Support
    parsed_summary = db.Column(db.Text, nullable=True)           # GAR summary of the quote
    extracted_data = db.Column(db.JSON, nullable=True)           # Structured fields, GAR-friendly
    parsing_status = db.Column(db.String(50), default='Pending') # Parsing lifecycle
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)     # pdf, ocr, etc.
    is_ai_processed = db.Column(db.Boolean, default=False)

    # 🧠 GAR Decision Support Fields
    ai_scorecard = db.Column(db.JSON, nullable=True)             # {"price": 9.1, "terms": 8.0, ...}
    ai_rank = db.Column(db.Integer, nullable=True)               # 1 = top-ranked by GAR
    is_ai_preferred = db.Column(db.Boolean, default=False)       # Flag for GAR’s preferred option
    reason_for_recommendation = db.Column(db.Text, nullable=True)# Human-readable explanation

    # ✅ Phase 2: GAR Interactivity
    gar_chat_ready = db.Column(db.Boolean, default=False)        # Can appear in GAR chat / Q&A
    gar_feedback = db.Column(db.Text, nullable=True)             # PM/Director feedback on GAR

    # 🔒 Security / Auditing
    is_archived = db.Column(db.Boolean, default=False)           # Soft-delete or deprecated quote
    visibility_roles = db.Column(db.String(255), default='Super Admin,Admin,Property Manager,Director')

    # 🔁 Relationships
    capex_request = db.relationship("CapexRequest", backref="responses")
    submitter = db.relationship("User", foreign_keys=[submitted_by], backref="capex_responses")

    def __repr__(self):
        return f"<CapexResponse by {self.contractor_name} - €{self.quote_amount}>"
