from datetime import datetime

from app.extensions import db


class JobDocket(db.Model):
    __tablename__ = "job_dockets"

    id = db.Column(db.Integer, primary_key=True)
    docket_number = db.Column(db.String(40), unique=True, nullable=True, index=True)
    contractor_job_number = db.Column(db.String(80), nullable=True)
    external_work_order_reference = db.Column(db.String(120), nullable=True, index=True)

    work_order_id = db.Column(db.Integer, db.ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=True, unique=True, index=True)
    contractor_id = db.Column(db.Integer, db.ForeignKey("contractors.id"), nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=True, index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey("units.id"), nullable=True, index=True)

    instruction_source = db.Column(db.String(80), nullable=False, default="Works Logix", index=True)
    standalone_client_name = db.Column(db.String(160), nullable=True)
    standalone_property_name = db.Column(db.String(160), nullable=True)
    standalone_address_line_1 = db.Column(db.String(160), nullable=True)
    standalone_address_line_2 = db.Column(db.String(160), nullable=True)
    standalone_town_city = db.Column(db.String(120), nullable=True)
    standalone_region = db.Column(db.String(120), nullable=True)
    standalone_postal_code = db.Column(db.String(40), nullable=True)
    standalone_country = db.Column(db.String(80), nullable=True)
    standalone_block_name = db.Column(db.String(120), nullable=True)
    standalone_core_name = db.Column(db.String(120), nullable=True)
    standalone_unit_number = db.Column(db.String(80), nullable=True)

    assigned_engineer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    assigned_engineer_ids = db.Column(db.JSON, nullable=True)
    assigned_team_id = db.Column(db.Integer, db.ForeignKey("contractor_teams.id"), nullable=True, index=True)

    status = db.Column(db.String(80), nullable=False, default="Accepted - Awaiting Scheduling", index=True)
    priority = db.Column(db.String(50), nullable=True)
    required_trade = db.Column(db.String(100), nullable=True)
    scope_of_works = db.Column(db.Text, nullable=True)
    access_notes = db.Column(db.Text, nullable=True)
    evidence_links = db.Column(db.JSON, nullable=True)
    attachments_count = db.Column(db.Integer, nullable=False, default=0)
    contact_name = db.Column(db.String(120), nullable=True)
    contact_phone = db.Column(db.String(50), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)

    scheduled_date = db.Column(db.Date, nullable=True, index=True)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    estimated_duration_minutes = db.Column(db.Integer, nullable=True)
    scheduling_notes = db.Column(db.Text, nullable=True)
    completion_date = db.Column(db.DateTime, nullable=True)

    chargeable = db.Column(db.Boolean, nullable=False, default=False)
    quotation_reference = db.Column(db.String(100), nullable=True)
    purchase_order_number = db.Column(db.String(100), nullable=True)
    invoice_status = db.Column(db.String(50), nullable=False, default="Not Ready")
    payment_status = db.Column(db.String(50), nullable=False, default="Not Invoiced")

    source_module = db.Column(db.String(80), nullable=False, default="Contractor Logix")
    gar_chat_ready = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    work_order = db.relationship("WorkOrder", back_populates="job_docket")
    contractor = db.relationship("Contractor", backref="job_dockets")
    company = db.relationship("Company")
    client = db.relationship("Client")
    unit = db.relationship("Unit")
    assigned_engineer = db.relationship("User", foreign_keys=[assigned_engineer_id])
    assigned_team = db.relationship("ContractorTeam", foreign_keys=[assigned_team_id])
    calendar_entries = db.relationship(
        "ContractorCalendarEntry",
        back_populates="job_docket",
        cascade="all, delete-orphan",
        order_by="ContractorCalendarEntry.scheduled_date",
    )
    private_work_logs = db.relationship(
        "JobDocketPrivateWorkLog",
        back_populates="job_docket",
        cascade="all, delete-orphan",
        order_by="desc(JobDocketPrivateWorkLog.work_date), desc(JobDocketPrivateWorkLog.created_at)",
    )

    def __repr__(self):
        return f"<JobDocket {self.docket_number or self.id} status={self.status}>"


class JobDocketPrivateWorkLog(db.Model):
    __tablename__ = "job_docket_private_work_logs"

    id = db.Column(db.Integer, primary_key=True)
    job_docket_id = db.Column(db.Integer, db.ForeignKey("job_dockets.id", ondelete="CASCADE"), nullable=False, index=True)
    contractor_id = db.Column(db.Integer, db.ForeignKey("contractors.id"), nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    work_date = db.Column(db.Date, nullable=False, default=lambda: datetime.utcnow().date(), index=True)
    labour_hours = db.Column(db.Numeric(8, 2), nullable=True)
    material_description = db.Column(db.String(255), nullable=True)
    material_quantity = db.Column(db.Numeric(10, 2), nullable=True)
    material_unit = db.Column(db.String(40), nullable=True)
    material_cost = db.Column(db.Numeric(10, 2), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    visibility_scope = db.Column(db.String(40), nullable=False, default="contractor_private")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    job_docket = db.relationship("JobDocket", back_populates="private_work_logs")
    contractor = db.relationship("Contractor")
    company = db.relationship("Company")
    created_by = db.relationship("User", foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<JobDocketPrivateWorkLog docket={self.job_docket_id} date={self.work_date}>"
