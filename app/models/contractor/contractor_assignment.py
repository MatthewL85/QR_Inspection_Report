# 📄 app/models/contractor/contractor_assignment.py

from app.extensions import db
from datetime import datetime

class ContractorAssignment(db.Model):
    __tablename__ = 'contractor_assignments'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    contractor_company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)  # contractor only

    # ✅ Visibility and preference controls
    is_preferred = db.Column(db.Boolean, default=False)
    allow_doc_sharing = db.Column(db.Boolean, default=True)  # GDPR toggle
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 📌 Optional metadata
    assigned_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # 🧠 Smart relationships (optional later)
    # ai_recommendation_score = db.Column(db.Float)
    # is_ai_suggested = db.Column(db.Boolean, default=False)
