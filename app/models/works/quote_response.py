from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB

class QuoteResponse(db.Model):
    __tablename__ = 'quote_responses'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_orders.id'), nullable=False)
    contractor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    submitted_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 📅 Metadata
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    quote_deadline = db.Column(db.DateTime, nullable=True)  # Optional override
    status = db.Column(db.String(50), default='Submitted')  # Submitted, Approved, Archived, Recalled
    decision_note = db.Column(db.Text)
    is_selected = db.Column(db.Boolean, default=False)

    # 📎 File Uploads
    quote_file_path = db.Column(db.String(255), nullable=False)  # Required PDF or DOC
    additional_files = db.Column(JSONB, nullable=True)  # {"drawings": "path1", "spec": "path2"}

    # 🧠 AI Parsing (Phase 1)
    parsed_total = db.Column(db.Numeric(10, 2), nullable=True)
    parsed_summary = db.Column(db.Text)
    parsed_items = db.Column(JSONB, nullable=True)  # [{"desc": "...", "qty": 2, "price": 150.00}]
    extracted_text = db.Column(db.Text)  # OCR or text extract
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    parsed_at = db.Column(db.DateTime, nullable=True)

    # 🔐 AI / GAR Evaluation
    ai_scorecard = db.Column(JSONB, nullable=True)  # {"clarity": 0.9, "price_fairness": 0.8, ...}
    ai_rank = db.Column(db.Integer)  # 1, 2, 3
    is_ai_preferred = db.Column(db.Boolean, default=False)
    reason_for_recommendation = db.Column(db.Text)

    # 🧠 GAR Integration
    gar_flagged = db.Column(db.Boolean, default=False)
    gar_alignment_score = db.Column(db.Float)
    gar_recommendation = db.Column(db.Text)
    gar_chat_enabled = db.Column(db.Boolean, default=False)
    gar_chat_notes = db.Column(db.Text)

    # 📎 Future Link: Invoice
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)

    # 📇 Template & Branding
    template_used = db.Column(db.String(100))  # 'default', 'company_a', etc.
    template_generated = db.Column(db.Boolean, default=False)
    template_generated_at = db.Column(db.DateTime, nullable=True)

    # 🧾 Audit & Visibility
    visible_to_admin = db.Column(db.Boolean, default=True)
    visible_to_creator = db.Column(db.Boolean, default=True)
    visibility_scope = db.Column(db.String(50), default='AssignedOnly')  # e.g., PMOnly, AssignedOnly, CompanyWide

    def __repr__(self):
        return f"<QuoteResponse id={self.id} contractor={self.contractor_id} status={self.status}>"
