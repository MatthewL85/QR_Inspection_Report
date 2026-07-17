# app/forms/contracts/contract_form.py
from __future__ import annotations

from typing import Any, Dict, Optional
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField, StringField, DateField, DecimalField, SelectField, HiddenField, TextAreaField
)
from wtforms.validators import DataRequired, Optional as Opt, Length

PPM_CHOICES = [
    ("Monthly", "Monthly"),
    ("Bi-Monthly", "Bi-Monthly"),
    ("Quarterly", "Quarterly"),
    ("Tri-Annual", "Tri-Annual"),
    ("Bi-Annual", "Bi-Annual"),
    ("Annually", "Annually"),
]

MONTH_CHOICES = [
    ("", "- Not set -"),
    ("January", "January"),
    ("February", "February"),
    ("March", "March"),
    ("April", "April"),
    ("May", "May"),
    ("June", "June"),
    ("July", "July"),
    ("August", "August"),
    ("September", "September"),
    ("October", "October"),
    ("November", "November"),
    ("December", "December"),
]

GAR_RISK_CHOICES = [
    ("", "- Not assessed -"),
    ("Low", "Low"),
    ("Medium", "Medium"),
    ("High", "High"),
    ("Critical", "Critical"),
]

class ContractForm(FlaskForm):
    """
    Classic contract form (optional). Not used by the schema-driven renew wizard,
    but useful for quick-create/edit flows or admin tools.

    Works with your latest model shape and the new prefill service payloads.
    """

    # Core context
    client_id = SelectField("Client", coerce=int, validators=[Opt()])  # supply choices in the route
    company_id = HiddenField(validators=[Opt()])                       # issuer company (if you want to carry it)

    template_version_id = HiddenField(validators=[Opt()])              # for classic flows (not the wizard)
    contract_title = StringField("Contract Title", validators=[DataRequired(), Length(max=255)])

    # Term
    start_date = DateField("Start Date", validators=[Opt()])
    end_date = DateField("End Date", validators=[Opt()])

    # Money
    currency = StringField("Currency", default="EUR", validators=[Opt(), Length(max=8)])
    contract_value = DecimalField("Base Fee (ex VAT)", places=2, rounding=None, validators=[Opt()])
    ppm_schedule = SelectField("PPM Schedule", choices=PPM_CHOICES, validators=[Opt()])

    # Renewal control
    target_management_fee = DecimalField("Target Management Fee", places=2, rounding=None, validators=[Opt()])
    annual_increase_percent = DecimalField("Annual Increase %", places=2, rounding=None, validators=[Opt()])
    renewal_month = SelectField("Renewal Month", choices=MONTH_CHOICES, validators=[Opt()])
    next_fee_increase_date = DateField("Next Fee Increase", validators=[Opt()])
    new_contract_drafted = BooleanField("New Contract Drafted")
    alert_owner_id = SelectField("Alert Owner", coerce=int, validators=[Opt()])
    last_reviewed_at = DateField("Last Reviewed", validators=[Opt()])
    gar_contract_risk_level = SelectField("GAR Risk Level", choices=GAR_RISK_CHOICES, validators=[Opt()])
    gar_contract_recommendation = TextAreaField("GAR Recommendation", validators=[Opt(), Length(max=4000)])
    renewal_notes = TextAreaField("Renewal Notes", validators=[Opt(), Length(max=4000)])

    # Primary contact (issuer/client-facing contact for this contract)
    primary_contact_name = StringField("Primary Contact Name", validators=[Opt(), Length(max=255)])
    primary_contact_email = StringField("Primary Contact Email", validators=[Opt(), Length(max=255)])
    primary_contact_phone = StringField("Primary Contact Phone", validators=[Opt(), Length(max=64)])

    # Optional: small notes area (can be used for admin remarks)
    notes = TextAreaField("Notes", validators=[Opt(), Length(max=4000)])

    # ---------------- convenience helpers ----------------

    def set_client_choices(self, pairs: list[tuple[int, str]], *, include_blank: bool = True) -> None:
        """Pass a list of (id, label)."""
        if include_blank and (not pairs or pairs[0][0] != 0):
            self.client_id.choices = [(0, "— Select client —")] + pairs
        else:
            self.client_id.choices = pairs

    def set_alert_owner_choices(self, pairs: list[tuple[int, str]], *, include_blank: bool = True) -> None:
        """Pass a list of internal users who can own renewal alerts."""
        if include_blank and (not pairs or pairs[0][0] != 0):
            self.alert_owner_id.choices = [(0, "- Not assigned -")] + pairs
        else:
            self.alert_owner_id.choices = pairs

    def apply_prefill_payload(self, payload: Dict[str, Any]) -> None:
        """
        Accepts the dict from app.services.contract.prefill.build_full_prefill_payload.
        Uses only safe, UI-visible bits; does not overwrite existing user input.
        """
        cf = (payload or {}).get("contract_fields", {}) if payload else {}

        def maybe_set(field, key):
            try:
                if hasattr(self, field):
                    fld = getattr(self, field)
                    if not (fld.data or "").strip():
                        fld.data = cf.get(key)
            except Exception:
                pass

        maybe_set("contract_title", "contract_title")
        maybe_set("currency", "currency")
        maybe_set("ppm_schedule", "ppm_schedule")
        maybe_set("primary_contact_name", "primary_contact_name")
        maybe_set("primary_contact_email", "primary_contact_email")
        maybe_set("primary_contact_phone", "primary_contact_phone")

    def mirror_from_instance(self, obj) -> None:
        """
        Populate fields from a model instance that has similarly-named attributes.
        Helpful for edit forms.
        """
        mapping = {
            "contract_title": "contract_title",
            "currency": "currency",
            "contract_value": "contract_value",
            "target_management_fee": "target_management_fee",
            "annual_increase_percent": "annual_increase_percent",
            "renewal_month": "renewal_month",
            "next_fee_increase_date": "next_fee_increase_date",
            "new_contract_drafted": "new_contract_drafted",
            "alert_owner_id": "alert_owner_id",
            "last_reviewed_at": "last_reviewed_at",
            "gar_contract_risk_level": "gar_contract_risk_level",
            "gar_contract_recommendation": "gar_contract_recommendation",
            "renewal_notes": "renewal_notes",
            "ppm_schedule": "ppm_schedule",
            "primary_contact_name": "primary_contact_name",
            "primary_contact_email": "primary_contact_email",
            "primary_contact_phone": "primary_contact_phone",
            "start_date": "start_date",
            "end_date": "end_date",
        }
        for form_field, attr in mapping.items():
            try:
                if hasattr(obj, attr) and hasattr(self, form_field):
                    getattr(self, form_field).data = getattr(obj, attr)
            except Exception:
                pass

    def to_dict(self) -> Dict[str, Any]:
        """
        Return a plain dict of the user-entered fields.
        Useful when you need to update a data_json or a model instance.
        """
        return {
            "client_id": self.client_id.data or None,
            "company_id": self.company_id.data or None,
            "template_version_id": self.template_version_id.data or None,
            "contract_title": (self.contract_title.data or "").strip(),
            "start_date": self.start_date.data,
            "end_date": self.end_date.data,
            "currency": (self.currency.data or "EUR").strip(),
            "contract_value": self.contract_value.data or 0,
            "target_management_fee": self.target_management_fee.data,
            "annual_increase_percent": self.annual_increase_percent.data,
            "renewal_month": self.renewal_month.data or None,
            "next_fee_increase_date": self.next_fee_increase_date.data,
            "new_contract_drafted": bool(self.new_contract_drafted.data),
            "alert_owner_id": self.alert_owner_id.data or None,
            "last_reviewed_at": self.last_reviewed_at.data,
            "gar_contract_risk_level": self.gar_contract_risk_level.data or None,
            "gar_contract_recommendation": (self.gar_contract_recommendation.data or "").strip(),
            "renewal_notes": (self.renewal_notes.data or "").strip(),
            "ppm_schedule": self.ppm_schedule.data or None,
            "primary_contact_name": (self.primary_contact_name.data or "").strip(),
            "primary_contact_email": (self.primary_contact_email.data or "").strip(),
            "primary_contact_phone": (self.primary_contact_phone.data or "").strip(),
            "notes": (self.notes.data or "").strip(),
        }
