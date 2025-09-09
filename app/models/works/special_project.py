from app.extensions import db
from datetime import datetime, date

class ClientSpecialProject(db.Model):
    __tablename__ = "client_special_projects"

    id        = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    contract_id = db.Column(db.Integer, db.ForeignKey("client_contracts.id"), nullable=True)

    project_name = db.Column(db.String(255), nullable=False)
    description  = db.Column(db.Text, nullable=True)

    contractor_id = db.Column(db.Integer, db.ForeignKey("contractors.id"), nullable=True)
    value         = db.Column(db.Numeric(12, 2), nullable=True)

    status     = db.Column(db.String(50), default="Open")  # Open|In Progress|Completed|Cancelled
    start_date = db.Column(db.Date, nullable=True)
    end_date   = db.Column(db.Date, nullable=True)

    # AI/GAR-ready notes (scope extraction / risks)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.Text, nullable=True)  # JSON
    reviewed_by_ai = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    client   = db.relationship("Client", backref="special_projects")
    contract = db.relationship("ClientContract", backref="special_projects")
    contractor = db.relationship("Contractor", backref="special_projects")

    def __repr__(self) -> str:
        return f"<ClientSpecialProject {self.project_name} client:{self.client_id}>"
